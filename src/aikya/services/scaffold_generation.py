"""Explicit resolve, staged execution and confirmed copy of known generator recipes."""
from aikya.code_index.policy import project_root,read_source
from aikya.core.state import locked
from aikya.review.contracts import encoded,digest
from aikya.review.definitions import selected_environment
from aikya.review.process import capture_process
from aikya.storage import atomic_write
from . import scaffold_recipes as recipes,scaffold_records as records,generation
from .documentation_inputs import profile
from .generation_inputs import sha


def preview(root,input_data,session_id):
    root=project_root(root);data=input_data
    if not isinstance(data,dict) or len(encoded(data))>8000:raise ValueError('Bounded scaffold JSON required')
    action=data.get('action');run_id=data.get('run_id');records.relative(run_id)
    source=records.source(root,session_id);p=profile(root)
    if p['project_type']!='development' or p['mode']!='new':raise ValueError('Scaffold is limited to new development projects')
    if action=='resolve':
        if set(data)-{'action','generator','run_id','version'} or not {'action','generator','run_id'}<=set(data):raise ValueError('Choose generator, run_id and optional exact version')
        if records.path(root,run_id,'record.json').exists():raise ValueError('Run identity already exists; inspect without replay')
        recipe=recipes.recipe(p,data['generator'],data.get('version'))
        review=dict(source=source,recipe=recipe,network='registry metadata/archive; no code execution' if recipe['package'] else 'none',
                    effects='private resolver record only',checks='not_run')
    elif action in ('prepare','copy'):
        allowed={'action','run_id'} if action=='prepare' else {'action','run_id','paths'}
        if set(data)!=allowed:raise ValueError('Unexpected scaffold input')
        record=records.load(root,run_id,session_id);recipe=record['recipe']
        if record['status']!=('resolved' if action=='prepare' else 'prepared'):
            raise ValueError('Only a resolved run may execute; copying requires prepared output')
        if recipes.recipe(p,recipe['id'],recipe['version'])!=recipe:raise ValueError('Generator executable or environment changed')
        if recipe['package'] and sha(read_source(root,records.relative(run_id)+'/generator.tgz',10000000))!=record['package']['sha256']:
            raise ValueError('Resolved generator archive changed')
        if action=='prepare':
            if record['status']!='resolved':raise ValueError('Only a resolved run may execute once')
            review=dict(source=source,recipe=recipe,package=record.get('package'),effects='execute known generator in private staging',
                        network='generator and package manager may access network and SDK caches',timeout_seconds=300,checks='not_run')
        else:
            if record['status']!='prepared':raise ValueError('No successfully prepared output to copy')
            files,_=records.outputs(root,run_id,record['manifest'],recipe=recipe);paths=data['paths']
            if not isinstance(paths,list) or not 1<=len(paths)<=100 or any(not isinstance(name,str) for name in paths) or len(set(paths))!=len(paths) or any(name not in files for name in paths):
                raise ValueError('Select known unique staged paths')
            result=generation.preview(root,{name:files[name] for name in paths},session_id,'scaffold',dict(run_id=run_id,process=record['process'],recipe=recipe['id']))
            if result['plan'] is None:return result
            review=result['review'];review['staged_manifest']=record['manifest']
            return dict(status='review_ready',plan=dict(input_data=data,session_id=session_id,source=source,record_hash=digest(record),generation=result['plan']),review=review)
        review['record_hash']=digest(record)
    else:raise ValueError('Choose resolve, prepare or copy')
    plan=dict(input_data=data,session_id=session_id,source=source,review_hash=digest(review))
    return dict(status='review_ready',plan=plan,review=review)


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit native scaffold confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or 'input_data' not in plan or 'session_id' not in plan:raise ValueError('Invalid scaffold plan')
    value=preview(root,plan['input_data'],plan['session_id'])
    if value['plan']!=plan:raise ValueError('Scaffold preview changed')
    data=plan['input_data'];run_id=data['run_id'];action=data['action'];session=plan['session_id']
    if action=='copy':
        record=records.load(root,run_id,session);files,_=records.outputs(root,run_id,record['manifest'],recipe=record['recipe'])
        return generation.apply(root,plan['generation'],{p:files[p] for p in data['paths']},approved=True)
    folder=records.path(root,run_id,'record.json').parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        fresh=preview(root,data,session)
        if fresh['plan']!=plan:raise ValueError('Scaffold source changed before effect')
        if action=='resolve':
            recipe=fresh['review']['recipe'];record=dict(run_id=run_id,status='resolving',source=plan['source'],recipe=recipe)
            records.save(root,run_id,record)
            if recipe['package']:
                raw,package=recipes.download(recipe)
                atomic_write(records.path(root,run_id,'generator.tgz'),raw,mode=0o600);record['package']=package
            if records.source(root,session)!=plan['source']:raise ValueError('Source changed during resolution; private outcome preserved')
            record['status']='resolved';records.save(root,run_id,record)
            return dict(status='resolved',run_id=run_id,recipe=recipe,package=record.get('package'),checks='not_run')
        record=records.load(root,run_id,session);record['status']='preparing';records.save(root,run_id,record)
        stage=records.workspace(root,run_id,record['recipe']);stage.mkdir(mode=0o700,parents=True)
        env=selected_environment();env.update(CI='1',npm_config_ignore_scripts='true',npm_config_cache=str(folder/'npm-cache'))
        argv=recipes.argv(record['recipe'],records.path(root,run_id,'generator.tgz'))
        process,_=capture_process(argv,stage,env,300,1048576,records.cancellation(root,run_id,session))
        record['process']=process;status=process['status']
        if status=='completed' and process['exit_code']==0:
            try:
                _,record['manifest']=records.outputs(root,run_id,recipe=record['recipe'])
                if records.source(root,session)!=record['source']:raise ValueError('Source changed during generator execution')
                status='prepared'
            except (ValueError,OSError):status='invalid_output'
        elif status=='completed':status='failed'
        try:
            recipe=record['recipe']
            if recipes.recipe(profile(root),recipe['id'],recipe['version'])!=recipe:status='definition_changed'
        except (ValueError,OSError):status='definition_changed'
        record['status']=status;records.save(root,run_id,record)
        return dict(status=status,run_id=run_id,process=process,manifest=record.get('manifest',[]),checks='not_run',delivery_authorized=False)


def cancel(root,run_id,session_id):
    root=project_root(root);value=records.load(root,run_id,session_id,current=False)
    if value['status'] not in ('resolved','preparing'):return dict(status='already_finished',run_id=run_id)
    from aikya.review import authentication
    payload=dict(run_id=run_id,session_id=session_id)
    atomic_write(records.path(root,run_id,'cancel.json'),encoded(authentication.seal(root,payload))+'\n',mode=0o600)
    return dict(status='cancellation_requested',run_id=run_id)


def inspect(root,run_id,session_id,path,offset=0,max_chars=1500):
    root=project_root(root);record=records.load(root,run_id,session_id)
    if record['status']!='prepared':raise ValueError('A prepared staged output is required')
    files,_=records.outputs(root,run_id,record['manifest'],recipe=record['recipe'])
    if path not in files or type(offset) is not int or offset<0 or type(max_chars) is not int or not 1<=max_chars<=6000:raise ValueError('Choose a bounded staged content window')
    text=files[path].decode('utf8');content=text[offset:offset+max_chars]
    return dict(path=path,sha256=sha(files[path]),offset=offset,content=content,next_offset=offset+len(content),truncated=offset+len(content)<len(text))


def status(root,run_id,session_id):
    root=project_root(root);record=records.load(root,run_id,session_id,current=False)
    try:current=records.source(root,session_id)==record['source']
    except (ValueError,OSError):current=False
    return dict(status=record['status'],run_id=run_id,current=current,recipe=record['recipe'],
                package=record.get('package'),process=record.get('process'),manifest=record.get('manifest',[]),checks='not_run')
