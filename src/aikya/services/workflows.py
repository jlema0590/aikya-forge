"""Host-neutral onboarding boundary; user-selected profile data is not inferred."""
from aikya.installation import portable,defaults
from aikya.discovery.layout import LAYOUTS
from aikya.review.contracts import encoded


def choices(root):
    return dict(project_types=list(defaults.PROJECT_TYPES),methodologies=['odd','sdd'],languages=['en','es'],
                backends=defaults.BACKENDS,frontends=defaults.FRONTENDS,mobile=defaults.MOBILES,
                mobile_frameworks=defaults.FRAMEWORKS,android_languages=['kotlin','java'],ios_ui=['swiftui','uikit'],layouts=list(LAYOUTS))


def preview(root,command,profile,language='en'):
    if command not in ('aikya-init','aikya-analyze','aikya-answers') or not isinstance(profile,dict):raise ValueError('Unknown onboarding command')
    if command=='aikya-answers' and len(encoded(profile))>8000:raise ValueError('Split oversized declarative profile input')
    mode=profile.get('mode') if command=='aikya-answers' else 'new' if command=='aikya-init' else 'existing'
    if mode not in ('new','existing'):raise ValueError('Declarative onboarding requires explicit mode')
    if profile.get('mode',mode)!=mode:raise ValueError('Onboarding command and project mode differ')
    plan=portable.preview(root,{**profile,'mode':mode},language=language)
    if command=='aikya-answers' and len(encoded(plan))>12000:raise ValueError('Declarative preview exceeds its host bound')
    return plan


def answers_preview(root,language=None):
    import hashlib
    from aikya.code_index.policy import project_root,read_source
    from aikya.review.contracts import parse
    root=project_root(root);raw=read_source(root,'.aikya/answers.json',12000)
    plan=preview(root,'aikya-answers',parse(raw),language)
    return dict(kind='answers_file',input_hash=hashlib.sha256(raw).hexdigest(),plan=plan)


def apply(root,plan,approved=False):
    if isinstance(plan,dict) and plan.get('kind')=='answers_file':
        if set(plan)!={'kind','input_hash','plan'} or answers_preview(root,plan['plan']['language'])!=plan:
            raise ValueError('Selected answers file changed')
        plan=plan['plan']
    return portable.apply(root,plan,approved=approved)
