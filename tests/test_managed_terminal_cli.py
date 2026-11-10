"""Managed launch previews bind both interpreters; support commands remain usable."""
from contextlib import redirect_stdout,redirect_stderr
import io,json
from pathlib import Path
from unittest.mock import patch
import unittest
import test_managed_terminal_resolution as fixtures
from aikya.cli import main as cli,terminal


class ManagedCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ManagedResolutionTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.project=self.fixture.root.parent/'project';self.project.mkdir()
        env=patch.dict('os.environ',{'AIKYA_INSTALL_ROOT':str(self.fixture.root)});env.start();self.addCleanup(env.stop)

    def invoke(self,entry,args):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err),patch('sys.stdin',io.StringIO()),patch.object(Path,'cwd',return_value=self.project):
            try:result=entry(args)
            except SystemExit as exited:result=exited.code
        return result,out.getvalue(),err.getvalue()

    def test_explicit_terminal_defaults_to_owned_node_and_python_without_execution(self):
        code,out,err=self.invoke(terminal.main,['--target',str(self.project),'--print-command','--resume','--provider','fixture','--model','fixture-model'])
        self.assertEqual(code,0,err);value=json.loads(out);payload=self.fixture.payload
        self.assertEqual(value['command'],[str(payload/'node/bin/node'),'--experimental-strip-types',str(payload/'runtime/src/launcher.ts'),
            '--target',str(self.project),'--python',str(payload/'python/bin/python3'),'--resume','--provider','fixture','--model','fixture-model'])
        self.assertEqual(list(self.project.iterdir()),[])

    def test_bare_aikya_reaches_the_managed_terminal_and_requires_a_tty(self):
        code,out,err=self.invoke(cli.main,[])
        self.assertEqual(code,2);self.assertIn('interactive terminal',err.lower())
        self.assertNotIn('Traceback',err);self.assertEqual(list(self.project.iterdir()),[])

    def test_default_terminal_flags_are_available_without_a_subcommand(self):
        code,out,err=self.invoke(cli.main,['--target',str(self.project),'--print-command'])
        self.assertEqual(code,0,err)
        self.assertEqual(json.loads(out)['command'][-2:],['--python',str(self.fixture.payload/'python/bin/python3')])
        self.assertEqual(list(self.project.iterdir()),[])

    def test_flag_before_a_legacy_support_command_still_probes_without_starting_a_terminal(self):
        code,out,err=self.invoke(cli.main,['--target',str(self.project),'probe'])
        self.assertEqual(code,0,err);self.assertEqual(json.loads(out)['target'],str(self.project))
        self.assertEqual(list(self.project.iterdir()),[])

    def test_help_does_not_validate_or_adopt_a_broken_activation(self):
        current=self.fixture.root/'terminal/current.json';current.write_text('{"custom":true}')
        code,out,err=self.invoke(cli.main,['--help'])
        self.assertEqual(code,0,err);self.assertIn('terminal',out)
        self.assertEqual(current.read_text(),'{"custom":true}');self.assertEqual(list(self.project.iterdir()),[])

    def test_malformed_legacy_loop_input_is_refused_without_source_or_session_effects(self):
        path=self.project/'loop.json';path.write_text('[]')
        try:code,out,err=self.invoke(cli.main,['feature','--target',str(self.project),'--agent-loop','--loop-input',str(path),'--approved'])
        except AttributeError:self.fail('Malformed loop JSON escaped CLI validation')
        self.assertEqual(code,2);self.assertNotIn('Traceback',err)
        self.assertEqual([p.name for p in self.project.iterdir()],['loop.json']);self.assertEqual(path.read_text(),'[]')

    def test_partial_provider_selection_is_refused_before_project_effects(self):
        code,out,err=self.invoke(terminal.main,['--provider','fixture','--target',str(self.project),'--print-command'])
        self.assertEqual(code,2);self.assertNotIn('Traceback',err);self.assertEqual(list(self.project.iterdir()),[])


if __name__=='__main__':unittest.main()
