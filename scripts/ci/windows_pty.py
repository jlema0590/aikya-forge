"""CI-only ConPTY transport; bounded queues and a job own every child process.

Uses Microsoft's pseudoconsole session contract. Separate pipe threads keep
ClosePseudoConsole draining even when a failing test stops consuming output.
"""
import ctypes as C
import os
import queue
import subprocess
import threading

HANDLE=C.c_void_p
DWORD=C.c_uint32
BOOL=C.c_int32
SIZE=C.c_size_t


class Coord(C.Structure):
    _fields_=[('X',C.c_int16),('Y',C.c_int16)]


class Startup(C.Structure):
    _fields_=[('cb',DWORD),('reserved',C.c_wchar_p),('desktop',C.c_wchar_p),('title',C.c_wchar_p),
        ('x',DWORD),('y',DWORD),('width',DWORD),('height',DWORD),('chars_x',DWORD),('chars_y',DWORD),
        ('fill',DWORD),('flags',DWORD),('show',C.c_uint16),('reserved_size',C.c_uint16),
        ('reserved_bytes',C.c_void_p),('stdin',HANDLE),('stdout',HANDLE),('stderr',HANDLE)]


class ExtendedStartup(C.Structure):
    _fields_=[('startup',Startup),('attributes',C.c_void_p)]


class Process(C.Structure):
    _fields_=[('process',HANDLE),('thread',HANDLE),('pid',DWORD),('tid',DWORD)]


class JobLimits(C.Structure):
    _fields_=[('process_time',C.c_int64),('job_time',C.c_int64),('flags',DWORD),
        ('min_working',SIZE),('max_working',SIZE),('active',DWORD),('affinity',SIZE),
        ('priority',DWORD),('scheduling',DWORD)]


class ExtendedJobLimits(C.Structure):
    _fields_=[('basic',JobLimits),('io',C.c_uint64*6),('process_memory',SIZE),('job_memory',SIZE),
        ('peak_process_memory',SIZE),('peak_job_memory',SIZE)]


class WindowsPty:
    def __init__(self,command,cwd,environment,columns,rows):
        if os.name!='nt':raise ValueError('ConPTY requires Windows')
        self.api=C.WinDLL('kernel32',use_last_error=True)
        signatures={
            'CreatePipe':(BOOL,[C.POINTER(HANDLE),C.POINTER(HANDLE),C.c_void_p,DWORD]),
            'CreatePseudoConsole':(C.c_int32,[Coord,HANDLE,HANDLE,DWORD,C.POINTER(HANDLE)]),
            'ResizePseudoConsole':(C.c_int32,[HANDLE,Coord]),'ClosePseudoConsole':(None,[HANDLE]),
            'InitializeProcThreadAttributeList':(BOOL,[C.c_void_p,DWORD,DWORD,C.POINTER(SIZE)]),
            'UpdateProcThreadAttribute':(BOOL,[C.c_void_p,DWORD,SIZE,C.c_void_p,SIZE,C.c_void_p,C.c_void_p]),
            'DeleteProcThreadAttributeList':(None,[C.c_void_p]),
            'CreateProcessW':(BOOL,[C.c_wchar_p,C.c_wchar_p,C.c_void_p,C.c_void_p,BOOL,DWORD,C.c_void_p,C.c_wchar_p,C.POINTER(ExtendedStartup),C.POINTER(Process)]),
            'CreateJobObjectW':(HANDLE,[C.c_void_p,C.c_wchar_p]),
            'SetInformationJobObject':(BOOL,[HANDLE,C.c_int32,C.c_void_p,DWORD]),
            'AssignProcessToJobObject':(BOOL,[HANDLE,HANDLE]),'ResumeThread':(DWORD,[HANDLE]),
            'GetExitCodeProcess':(BOOL,[HANDLE,C.POINTER(DWORD)]),
            'TerminateProcess':(BOOL,[HANDLE,DWORD]),'CloseHandle':(BOOL,[HANDLE]),
            'ReadFile':(BOOL,[HANDLE,C.c_void_p,DWORD,C.POINTER(DWORD),C.c_void_p]),
            'WriteFile':(BOOL,[HANDLE,C.c_void_p,DWORD,C.POINTER(DWORD),C.c_void_p]),
        }
        for name,(result,arguments) in signatures.items():
            function=getattr(self.api,name);function.restype=result;function.argtypes=arguments
        self.handles={};self.console=HANDLE();self.attributes=None;self.attributes_ready=False;self.process=Process()
        self.incoming=queue.Queue(maxsize=32);self.outgoing=queue.Queue(maxsize=16)
        self.closing=threading.Event();self.overflow=threading.Event();self.eof=threading.Event()
        self.reader=None;self.writer=None;self.assigned=False
        try:self._start(command,cwd,environment,columns,rows)
        except BaseException:self.close();raise

    @staticmethod
    def _check(result):
        if not result:raise C.WinError(C.get_last_error())

    @staticmethod
    def _hresult(result):
        if result<0:raise OSError('ConPTY operation failed: '+hex(result & 0xffffffff))

    def _close_handle(self,name):
        handle=self.handles.pop(name,None)
        if handle:self.api.CloseHandle(handle)

    def _start(self,command,cwd,environment,columns,rows):
        for first,second in [('input_read','input_write'),('output_read','output_write')]:
            read=HANDLE();write=HANDLE();self._check(self.api.CreatePipe(C.byref(read),C.byref(write),None,0))
            self.handles[first]=read;self.handles[second]=write
        self._hresult(self.api.CreatePseudoConsole(Coord(columns,rows),self.handles['input_read'],self.handles['output_write'],0,C.byref(self.console)))
        size=SIZE();self.api.InitializeProcThreadAttributeList(None,1,0,C.byref(size))
        if not 0<size.value<65536:raise ValueError('Invalid ConPTY attribute size')
        self.attributes=C.create_string_buffer(size.value)
        self._check(self.api.InitializeProcThreadAttributeList(self.attributes,1,0,C.byref(size)))
        self.attributes_ready=True
        self._check(self.api.UpdateProcThreadAttribute(self.attributes,0,0x00020016,self.console,C.sizeof(HANDLE),None,None))
        startup=ExtendedStartup();startup.startup.cb=C.sizeof(ExtendedStartup)
        # Explicit NULL handles prevent the redirected CI streams being duplicated
        # into the child instead of its pseudoconsole (microsoft/terminal #15814).
        startup.startup.flags=0x100
        startup.attributes=C.cast(self.attributes,C.c_void_p)
        job=self.api.CreateJobObjectW(None,None);self._check(job);self.handles['job']=job
        limits=ExtendedJobLimits();limits.basic.flags=0x2000
        self._check(self.api.SetInformationJobObject(job,9,C.byref(limits),C.sizeof(limits)))
        block=C.create_unicode_buffer('\0'.join(key+'='+str(value) for key,value in sorted(environment.items(),key=lambda pair:pair[0].upper()))+'\0\0')
        line=C.create_unicode_buffer(subprocess.list2cmdline(command))
        self._check(self.api.CreateProcessW(command[0],line,None,None,False,0x00080000|0x00000400|0x4,block,str(cwd),C.byref(startup),C.byref(self.process)))
        self.handles['process']=self.process.process;self.handles['thread']=self.process.thread
        self._check(self.api.AssignProcessToJobObject(job,self.process.process));self.assigned=True
        self._close_handle('input_read');self._close_handle('output_write')
        self.reader=threading.Thread(target=self._read_pipe,daemon=True);self.reader.start()
        self.writer=threading.Thread(target=self._write_pipe,daemon=True);self.writer.start()
        if self.api.ResumeThread(self.process.thread)==0xffffffff:raise C.WinError(C.get_last_error())
        self._close_handle('thread')

    def _read_pipe(self):
        buffer=C.create_string_buffer(4096);count=DWORD()
        try:
            while self.api.ReadFile(self.handles['output_read'],buffer,4096,C.byref(count),None) and count.value:
                if self.closing.is_set():continue
                try:self.incoming.put_nowait(buffer.raw[:count.value])
                except queue.Full:self.overflow.set()
        finally:self.eof.set()

    def _write_pipe(self):
        while not self.closing.is_set():
            try:value=self.outgoing.get(timeout=.05)
            except queue.Empty:continue
            count=DWORD();buffer=C.create_string_buffer(value)
            if not self.api.WriteFile(self.handles['input_write'],buffer,len(value),C.byref(count),None) or count.value!=len(value):return

    def read(self,wait):
        if self.overflow.is_set():raise ValueError('ConPTY output exceeds its queue bound')
        try:return self.incoming.get(timeout=wait)
        except queue.Empty:return b''

    def write(self,value):
        if len(value)>2048:raise ValueError('ConPTY input exceeds its byte bound')
        try:self.outgoing.put_nowait(value)
        except queue.Full:raise ValueError('ConPTY input exceeds its queue bound') from None

    def resize(self,columns,rows):
        self._hresult(self.api.ResizePseudoConsole(self.console,Coord(columns,rows)))

    def _close_console(self):
        if self.console.value:
            self.api.ClosePseudoConsole(self.console);self.console=HANDLE()

    def poll(self):
        code=DWORD();self._check(self.api.GetExitCodeProcess(self.process.process,C.byref(code)))
        if code.value==259:return None
        self._close_console()
        if self.reader:self.reader.join(timeout=3)
        if self.reader and self.reader.is_alive():raise TimeoutError('ConPTY output did not close')
        return code.value

    def close(self):
        self.closing.set()
        if self.process.process and not self.assigned:self.api.TerminateProcess(self.process.process,1)
        self._close_handle('job')
        self._close_console()
        self._close_handle('input_read');self._close_handle('output_write')
        for thread in (self.reader,self.writer):
            if thread:thread.join(timeout=3)
        for name in list(self.handles):self._close_handle(name)
        if self.attributes_ready:self.api.DeleteProcThreadAttributeList(self.attributes);self.attributes_ready=False
        self.attributes=None
