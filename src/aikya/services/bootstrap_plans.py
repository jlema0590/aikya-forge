"""Read-only bootstrap facts and canonical generator projections."""
from pathlib import Path
import tempfile
from aikya.code_index.policy import read_source,excluded
from aikya.core.checkpoints import safe_file
from aikya.documentation.composition import slug_value
from aikya.documentation.layout import stamp
from aikya.review.contracts import identifier,encoded,digest
from aikya.tools import scaffold,infrastructure
from .documentation_inputs import profile


def text(value,label,limit=1000):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(c)<32 and c not in '\n\t' for c in value):raise ValueError('Explicit bounded '+label+' required')
    return value.strip()


def source_path(root,name):
    path=safe_file(root,name)
    if (excluded(name) or any(p.lower() in ('.codex','.agents','.pi') for p in name.split('/'))
            or path.name.upper() in ('AGENTS.MD','CLAUDE.MD','SKILL.MD') or name.startswith('aikya/docs/')):
        raise ValueError('Protected bootstrap source path')
    return path


def project(root,data):
    fields={'action','slug','objective','modules','files','acceptance','checks'}
    if set(data)!=fields:raise ValueError('Project plan requires slug/objective/modules/files/acceptance/checks')
    p=profile(root)
    if p['project_type']!='development':raise ValueError('Use infrastructure workflow for this profile')
    slug=slug_value(data['slug']);objective=text(data['objective'],'project objective')
    modules=data['modules'];files=data['files'];acceptance=data['acceptance'];checks=data['checks']
    if not isinstance(modules,list) or not 1<=len(modules)<=20:raise ValueError('Explicit modules required')
    rows=[];names=set()
    for item in modules:
        if not isinstance(item,dict) or set(item)!={'name','path','purpose'}:raise ValueError('Module requires name/path/purpose')
        name=identifier(item['name']);relative=item['path']
        if name in names or not isinstance(relative,str):raise ValueError('Unique named modules required')
        names.add(name)
        if relative!='.':source_path(root,relative+'/.aikya-module-marker')
        folder=root/relative
        if folder.exists() and not folder.is_dir():raise ValueError('Module path must describe a directory')
        rows.append(dict(name=name,path=relative,purpose=text(item['purpose'],'module purpose',300)))
    if not isinstance(files,list) or not 1<=len(files)<=20 or len(set(files))!=len(files):raise ValueError('Select 1–20 proposed files')
    for path in files:source_path(root,path)
    if not isinstance(acceptance,list) or not 1<=len(acceptance)<=10:raise ValueError('Observable acceptance required')
    acceptance=[text(item,'acceptance criterion',300) for item in acceptance]
    if not isinstance(checks,list) or not 1<=len(checks)<=10 or len(set(checks))!=len(checks):raise ValueError('Named checks required')
    checks=[identifier(item) for item in checks]
    return dict(slug=slug,objective=objective,modules=rows,files=files,acceptance=acceptance,checks=checks,
                methodology=p['methodology'],mode=p['mode'],execution='not_run',implementation_authorized=False)


def project_document(review,language):
    es=language=='es'
    body='# '+('Plan del proyecto' if es else 'Project plan')+' — '+review['slug']+'\n\n'
    body+=('Plan registrado; no se ha implementado ni probado la aplicación.' if es else 'Recorded plan; the application has not been implemented or tested.')
    body+='\n\n## '+('Objetivo' if es else 'Objective')+'\n\n'+review['objective']+'\n\n```json\n'+encoded(review)+'\n```'
    return stamp(body).encode()


def infra(root,p,language):
    # Legacy planners read only bounded captured manifest inputs in an isolated tree.
    captured={};directories=[];total=0
    for prefix in ('','apps/api','apps/web','apps/frontend','apps/mobile'):
        folder=root/prefix
        safe_file(root,(prefix+'/' if prefix else '')+'.aikya-input-marker')
        if not folder.is_dir():continue
        directories.append(prefix)
        for name in ('package.json','package-lock.json','.nvmrc','pom.xml','mvnw','requirements.txt','Dockerfile'):
            relative=(prefix+'/' if prefix else '')+name;target=safe_file(root,relative)
            if target.exists():
                raw=read_source(root,relative,1000000);total+=len(raw)
                if total>5000000:raise ValueError('Infrastructure manifest inputs exceed 5 MB')
                captured[relative]=raw
    chart=p['infrastructure'].get('helm_chart_path')
    if chart:
        name=chart+'/Chart.yaml';source_path(root,name)
        if safe_file(root,name).exists():captured[name]=read_source(root,name,1000000)
    with tempfile.TemporaryDirectory(prefix='aikya-infra-plan-') as tmp:
        stage=Path(tmp)
        for prefix in directories:(stage/prefix).mkdir(parents=True,exist_ok=True)
        for name,raw in captured.items():
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        files,pending=infrastructure.specs(stage,p)
    for name,raw in captured.items():
        if read_source(root,name,1000000)!=raw:raise ValueError('Infrastructure inputs changed during inspection')
    result={name:body.encode() for name,body in files.items() if not name.lower().endswith('.md')}
    if files:
        es=language=='es';body='# '+('Propuesta de infraestructura' if es else 'Infrastructure proposal')+'\n\n'
        body+=('Se han propuesto archivos locales; no se han ejecutado operaciones remotas ni desplegado infraestructura.' if es else
               'Local files are proposed. Remote operations and deployment: not executed.')
        body+='\n\n```json\n'+encoded(dict(profile=p['infrastructure'],artifacts=sorted(result),pending_confirmations=len(pending)))+'\n```'
        result['aikya/docs/infrastructure/bootstrap.md']=stamp(body).encode()
    return result,dict(pending=pending,manifest_inputs={name:digest(raw.hex()) for name,raw in captured.items()},
                       remote_operations='not_authorized')


def scaffold_plan(p):
    commands,manual=scaffold.command_plans(p)
    rows=[]
    for index,item in enumerate(commands):
        dynamic=any('@latest' in token for token in item['command'])
        rows.append(dict(id='generator-'+str(index+1),label=item['label'],command=item['command'],destination=item['creates'],requires=item['requires'],status='version_required' if dynamic else 'probe_required'))
    return dict(generators=rows,manual=manual,execution='not_run',mode=p['mode'])
