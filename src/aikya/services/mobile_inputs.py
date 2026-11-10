"""Selected recorded mobile platforms and read-only SDK presence, not acceptance."""
import platform
import shutil
from aikya.installation.requirements import required_tools,command_version
from .bootstrap_plans import source_path
from .documentation_inputs import profile


def selection(root,platforms):
    p=profile(root)
    if p['project_type']!='development' or p['mobile']=='none':raise ValueError('A recorded mobile development profile is required')
    allowed={'android','ios'} if p['mobile']=='both' else {p['mobile']}
    if (not isinstance(platforms,list) or not 1<=len(platforms)<=2 or any(not isinstance(value,str) for value in platforms)
            or len(set(platforms))!=len(platforms) or not set(platforms)<=allowed):raise ValueError('Choose unique platforms inside the project profile')
    return p,sorted(platforms)


def scope(root,files,platforms):
    if (not isinstance(files,list) or not 1<=len(files)<=20 or any(not isinstance(name,str) for name in files)
            or len(set(files))!=len(files)):raise ValueError('Select 1–20 unique mobile task paths')
    for name in files:
        source_path(root,name)
        for other in {'android','ios'}-set(platforms):
            if name.startswith((other+'/', 'apps/'+other+'/')):raise ValueError('Task path targets an unselected mobile platform')
    return sorted(files)


def context(p,platforms):
    mobile='both' if len(platforms)==2 else platforms[0]
    required=required_tools(dict(backend='none',frontend='none',mobile=mobile,mobile_framework=p['mobile_framework'],package_manager=p['package_manager']))
    rows=[]
    for name in required:
        if name=='android-sdk':
            version,_=command_version(name);presence='found' if version else 'missing'
        elif name=='xcodebuild' and platform.system()!='Darwin':presence='unsupported_host'
        else:presence='found' if shutil.which(name) else 'missing'
        rows.append(dict(tool=name,presence=presence,compatibility='not_verified',version=None))
    return dict(platforms=platforms,framework=p['mobile_framework'],toolchains=rows,
                readiness='not_configured' if any(row['presence']!='found' for row in rows) else 'unverified',
                compatibility='not_verified',build='not_run',tests='not_run',simulator='not_checked',acceptance='not_verified',
                recorded_profile=True,source_execution=False)
