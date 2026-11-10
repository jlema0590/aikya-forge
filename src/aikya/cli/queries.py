"""Read-only legacy project and execution status queries."""
import json
import aikya.installation.facade as installer


def query(args,target):
    if args.command=='probe':
        detected=installer.detect_project(target) if target.exists() else {'modules':[],'findings':['New directory']}
        print(json.dumps({'target':str(target),'detected':detected,
                          'existing_profile':installer.read_json_safe(target/'.harness/project-profile.json'),
                          'aikya_bootstrap':(target/'.aikya/bootstrap.json').is_file()},ensure_ascii=False,indent=2))
        return 0
    if args.command=='status':
        from aikya.core.state import read_active
        from aikya.middleware.metrics import read_metrics
        from aikya.middleware.statusline import render_status
        context={'root':str(target),'session_id':args.session}
        if args.execution_details:
            print(render_status(read_active(context) or {},read_metrics(context),width=180,detail=True));return 0
        print(json.dumps({'configured':(target/'.harness/project-profile.json').is_file(),
           'docs':(target/'aikya/docs/README.md').is_file(),
           'answers':(target/'.aikya/answers.json').is_file()},indent=2))
        return 0
