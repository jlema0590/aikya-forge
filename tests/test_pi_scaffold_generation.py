"""Confirmed known generators execute in staging before a separately reviewed copy."""
import importlib,json,os,stat,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from pi_tool_fixture import tool_path,write_tool
try:scaffold=importlib.import_module('aikya.services.scaffold_generation')
except ModuleNotFoundError:scaffold=None


class ScaffoldGenerationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(scaffold,'Native staged generator service is absent')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);base=Path(self.tmp.name).resolve()
        self.root=base/'project';self.root.mkdir();self.bin=base/'bin';self.bin.mkdir()
        (self.root/'.harness').mkdir();self.profile()
        self.tool=tool_path(self.bin,'dotnet');self.program("from pathlib import Path\nPath('Program.cs').write_text('class App {}\\n')\nprint('created')\n")
        self.env=patch.dict(os.environ,{'PATH':str(self.bin)+os.pathsep+os.environ.get('PATH','')});self.env.start();self.addCleanup(self.env.stop)

    def profile(self,**changes):
        data=dict(backend='dotnet',backend_framework='minimal-api',methodology='odd',mode='new',repository_layout='singlerepo');data.update(changes)
        (self.root/'.harness/project-profile.json').write_text(json.dumps(dict(decisions=data)))

    def program(self,body):
        write_tool(self.tool,body)

    def preview(self,**data):return scaffold.preview(self.root,data,'author-session')

    def resolve(self,run_id='run-one'):
        value=self.preview(action='resolve',generator='generator-1',run_id=run_id)
        return scaffold.apply(self.root,value['plan'],approved=True)

    def prepare(self):
        self.resolve();value=self.preview(action='prepare',run_id='run-one')
        return scaffold.apply(self.root,value['plan'],approved=True)

    def test_preview_never_executes_and_both_staging_and_copy_require_confirmation(self):
        value=self.preview(action='resolve',generator='generator-1',run_id='run-one')
        self.assertFalse((self.root/'.aikya').exists())
        with self.assertRaises(ValueError):scaffold.apply(self.root,value['plan'])
        self.resolve();value=self.preview(action='prepare',run_id='run-one')
        self.assertFalse((self.root/'Program.cs').exists())
        with self.assertRaises(ValueError):scaffold.apply(self.root,value['plan'])
        result=scaffold.apply(self.root,value['plan'],approved=True)
        self.assertEqual(result['status'],'prepared');self.assertEqual(result['process']['exit_code'],0)
        self.assertFalse((self.root/'Program.cs').exists())
        value=self.preview(action='copy',run_id='run-one',paths=['Program.cs'])
        with self.assertRaises(ValueError):scaffold.apply(self.root,value['plan'])
        result=scaffold.apply(self.root,value['plan'],approved=True)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['checks'],'not_run')
        self.assertEqual((self.root/'Program.cs').read_text(),'class App {}\n')
        with self.assertRaises(ValueError):scaffold.apply(self.root,value['plan'],approved=True)

    def test_project_helper_is_not_imported_and_owner_files_are_preserved(self):
        helper=self.root/'aikya/scripts/harness/aikya_requirements.py';helper.parent.mkdir(parents=True)
        helper.write_text("raise RuntimeError('untrusted project helper')\n")
        self.prepare();(self.root/'Program.cs').write_text('OWNER\n')
        # A source change invalidates the staged run; it cannot overwrite the owner.
        with self.assertRaises(ValueError):self.preview(action='copy',run_id='run-one',paths=['Program.cs'])
        self.assertEqual((self.root/'Program.cs').read_text(),'OWNER\n')

    def test_changed_binary_or_profile_refuses_launch(self):
        self.resolve();value=self.preview(action='prepare',run_id='run-one')
        self.program("raise SystemExit(9)\n")
        with self.assertRaises(ValueError):scaffold.apply(self.root,value['plan'],approved=True)
        self.assertFalse((self.root/'Program.cs').exists())
        self.profile(mode='existing')
        with self.assertRaises(ValueError):self.preview(action='resolve',generator='generator-1',run_id='another')

    def test_missing_sdk_and_unknown_recipes_are_not_success(self):
        self.tool.unlink()
        with patch.dict(os.environ,{'PATH':str(self.bin)}):
            with self.assertRaises(ValueError):self.preview(action='resolve',generator='generator-1',run_id='missing')
        with self.assertRaises(ValueError):self.preview(action='resolve',generator='shell',run_id='bad')
        self.assertFalse((self.root/'.aikya').exists())

    def test_dotnet_uses_the_explicit_profile_name_instead_of_the_private_workspace(self):
        self.profile(name='Jourpass.Api')
        self.program("from pathlib import Path\nimport sys\na=sys.argv\nname=a[a.index('--name')+1] if '--name' in a else Path.cwd().name\nPath(name+'.csproj').write_text('<Project />')\n")
        result=self.prepare();self.assertEqual(result['status'],'prepared')
        self.assertIn('Jourpass.Api.csproj',[row['path'] for row in result['manifest']])
        self.assertNotIn('workspace.csproj',[row['path'] for row in result['manifest']])

    def test_unsupported_project_names_are_refused_before_resolution_or_execution(self):
        for name in ('../escape','--option','user/project','a'*81):
            self.profile(name=name)
            with self.subTest(name=name),self.assertRaises(ValueError):
                self.preview(action='resolve',generator='generator-1',run_id='named-project')
        self.assertFalse((self.root/'.aikya').exists())

    def test_npm_single_repo_uses_the_reviewed_profile_name_for_its_working_directory(self):
        from aikya.services import scaffold_recipes
        self.profile(backend='none',backend_framework='none',frontend='react',name='jourpass-ui')
        self.tool=tool_path(self.bin,'npm')
        self.program("from pathlib import Path\nimport json\nPath('package.json').write_text(json.dumps(dict(name=Path.cwd().name)))\n")
        package=dict(name='create-vite',version='8.0.0',tarball='https://registry.npmjs.org/create-vite/-/create-vite-8.0.0.tgz',
                     integrity='sha512-fixture',sha256=__import__('hashlib').sha256(b'fixture archive').hexdigest())
        value=self.preview(action='resolve',generator='generator-1',run_id='npm-name',version='8.0.0')
        with patch.object(scaffold_recipes,'download',return_value=(b'fixture archive',package)):
            scaffold.apply(self.root,value['plan'],approved=True)
        value=self.preview(action='prepare',run_id='npm-name');result=scaffold.apply(self.root,value['plan'],approved=True)
        self.assertEqual(result['status'],'prepared')
        view=scaffold.inspect(self.root,'npm-name','author-session','package.json')
        self.assertEqual(json.loads(view['content'])['name'],'jourpass-ui')

    def test_failed_empty_and_linked_outputs_are_not_ready_for_copy(self):
        for index,body in enumerate(("raise SystemExit(7)\n","print('nothing')\n","from pathlib import Path\nPath('escape').symlink_to('/tmp')\n")):
            with self.subTest(index=index):
                self.program(body);run_id='failed-'+str(index);self.resolve(run_id)
                value=self.preview(action='prepare',run_id=run_id);result=scaffold.apply(self.root,value['plan'],approved=True)
                self.assertNotEqual(result['status'],'prepared')
                with self.assertRaises(ValueError):self.preview(action='copy',run_id=run_id,paths=['Program.cs'])
        self.assertFalse((self.root/'Program.cs').exists())

    def test_cancelled_before_launch_does_not_execute_or_allow_replay(self):
        self.resolve();value=self.preview(action='prepare',run_id='run-one')
        result=scaffold.cancel(self.root,'run-one','author-session');self.assertEqual(result['status'],'cancellation_requested')
        result=scaffold.apply(self.root,value['plan'],approved=True)
        self.assertEqual(result['status'],'cancelled');self.assertFalse((self.root/'Program.cs').exists())
        with self.assertRaises(ValueError):scaffold.apply(self.root,value['plan'],approved=True)

    def test_staged_content_tampering_blocks_copy_and_inspection_is_bounded(self):
        result=self.prepare();self.assertEqual(result['status'],'prepared')
        view=scaffold.inspect(self.root,'run-one','author-session','Program.cs',0,12)
        self.assertEqual(view['content'],'class App {}');self.assertTrue(view['truncated'])
        stage=self.root/'.aikya/pi/scaffold/run-one/workspace/Program.cs';stage.write_text('class Replaced {}\n')
        with self.assertRaises(ValueError):self.preview(action='copy',run_id='run-one',paths=['Program.cs'])
        self.assertFalse((self.root/'Program.cs').exists())

    def test_unresolved_versions_and_existing_projects_cannot_execute(self):
        self.profile(backend='next',backend_framework='next-app-router',frontend='react')
        with self.assertRaises(ValueError):self.preview(action='resolve',generator='generator-1',run_id='npm-run')
        for version in ('latest','1.0.0; echo bad','https://example.com'):
            with self.assertRaises(ValueError):self.preview(action='resolve',generator='generator-1',run_id='npm-run',version=version)
        self.profile(mode='existing')
        with self.assertRaises(ValueError):self.preview(action='resolve',generator='generator-1',run_id='old')

    def test_pinned_registry_download_is_verified_before_a_generator_can_execute(self):
        import base64,hashlib,io
        self.profile(backend='next',backend_framework='next-app-router',frontend='react')
        npm=tool_path(self.bin,'npm');write_tool(npm,'raise SystemExit(99)\n')
        archive=b'reviewed external archive';url='https://registry.npmjs.org/create-next-app/-/create-next-app-1.2.3.tgz'
        integrity='sha512-'+base64.b64encode(hashlib.sha512(archive).digest()).decode()
        metadata=json.dumps(dict(name='create-next-app',version='1.2.3',dist=dict(tarball=url,integrity=integrity))).encode()
        value=self.preview(action='resolve',generator='generator-1',run_id='pinned',version='1.2.3')
        self.assertFalse((self.root/'.aikya').exists())
        class Response(io.BytesIO):
            def geturl(self):return self.url
        def download(request,**kwargs):
            target=request.full_url if hasattr(request,'full_url') else request
            self.assertIn(target,('https://registry.npmjs.org/create-next-app/1.2.3',url))
            result=Response(archive if target==url else metadata);result.url=target;return result
        with patch('urllib.request.urlopen',side_effect=download):result=scaffold.apply(self.root,value['plan'],approved=True)
        self.assertEqual(result['status'],'resolved');self.assertEqual(result['package']['integrity'],integrity)
        self.assertEqual((self.root/'.aikya/pi/scaffold/pinned/generator.tgz').read_bytes(),archive)
        self.assertFalse((self.root/'package.json').exists())
        # A modified cached archive must never reach the npm executable.
        (self.root/'.aikya/pi/scaffold/pinned/generator.tgz').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.preview(action='prepare',run_id='pinned')

    def test_sdd_without_current_task_cannot_resolve_or_launch(self):
        self.profile(methodology='sdd')
        with self.assertRaises(ValueError):self.preview(action='resolve',generator='generator-1',run_id='unapproved')
        self.assertFalse((self.root/'.aikya').exists())

    def test_cancellation_still_works_after_source_drift(self):
        self.resolve();(self.root/'owner.cs').write_text('class Owner {}\n')
        self.assertEqual(scaffold.cancel(self.root,'run-one','author-session')['status'],'cancellation_requested')
        with self.assertRaises(ValueError):scaffold.cancel(self.root,'run-one','foreign-session')

    def test_active_process_cancellation_waits_for_observed_exit(self):
        import threading,time
        self.program("import time\nfrom pathlib import Path\nPath('started').write_text('yes')\ntime.sleep(20)\nPath('late').write_text('no')\n")
        self.resolve();value=self.preview(action='prepare',run_id='run-one');outcome={}
        def work():outcome['result']=scaffold.apply(self.root,value['plan'],approved=True)
        thread=threading.Thread(target=work);thread.start()
        try:
            deadline=time.monotonic()+4
            while not (self.root/'.aikya/pi/scaffold/run-one/workspace/started').exists() and time.monotonic()<deadline:time.sleep(.02)
            self.assertTrue((self.root/'.aikya/pi/scaffold/run-one/workspace/started').exists())
            scaffold.cancel(self.root,'run-one','author-session');thread.join(4)
            self.assertFalse(thread.is_alive());self.assertEqual(outcome['result']['status'],'cancelled')
            self.assertIsNotNone(outcome['result']['process']['exit_code'])
            self.assertFalse((self.root/'.aikya/pi/scaffold/run-one/workspace/late').exists())
        finally:
            scaffold.cancel(self.root,'run-one','author-session');thread.join(25)

    @unittest.skipIf(os.name=='nt','Windows locks the running command wrapper; executable drift is covered before launch')
    def test_generator_binary_drift_during_execution_is_not_prepared(self):
        self.program("from pathlib import Path\nPath('Program.cs').write_text('class App {}\\n')\nPath(__file__).write_text('changed during execution')\n")
        result=self.prepare();self.assertEqual(result['status'],'definition_changed')
        with self.assertRaises(ValueError):self.preview(action='copy',run_id='run-one',paths=['Program.cs'])

    def test_bad_registry_metadata_cannot_become_a_resolved_executable(self):
        import io
        self.profile(backend='next',backend_framework='next-app-router',frontend='react')
        write_tool(tool_path(self.bin,'npm'),'raise SystemExit(99)\n')
        class Response(io.BytesIO):
            def geturl(self):return 'https://registry.npmjs.org/create-next-app/1.2.3'
        for i,dist in enumerate((None,{},dict(tarball='https://example.com/other.tgz',integrity='sha512-bad'))):
            run_id='bad-package-'+str(i);value=self.preview(action='resolve',generator='generator-1',run_id=run_id,version='1.2.3')
            response=Response(json.dumps(dict(name='create-next-app',version='1.2.3',dist=dist)).encode())
            with patch('urllib.request.urlopen',return_value=response):
                with self.assertRaises(ValueError):scaffold.apply(self.root,value['plan'],approved=True)
            status=scaffold.status(self.root,run_id,'author-session');self.assertEqual(status['status'],'resolving')
            with self.assertRaises(ValueError):self.preview(action='prepare',run_id=run_id)
