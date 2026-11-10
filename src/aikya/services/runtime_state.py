"""Trusted local-host accounting API; not registered as a model tool or consent."""
import argparse
import json
import sys
from pathlib import Path
from aikya.code_index.policy import project_root
from aikya.routing import pi_usage
from aikya.installation import migration_v8
from . import review,workflows,task_binding,sdd,maintenance,checks,check_cancel,odd_workflow,selected_skills,diagnostics,documentation,project_bootstrap,scaffold_generation,infra_validation,engineering_workflows
from . import documentation_recovery
from . import batch_recovery,task_runs,skill_management,skill_fetch
from aikya.review.contracts import parse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path); args = parser.parse_args(argv)
    root = project_root(args.root)
    try:
        raw = sys.stdin.buffer.read(16385)
        if len(raw) > 16384: raise ValueError('Request too large')
        request = parse(raw)
        if not isinstance(request, dict) or set(request) != {'action', 'arguments'} or not isinstance(request['arguments'], dict):
            raise ValueError('Invalid host request')
        operations = dict(status=pi_usage.status, configure=pi_usage.configure, adjust=pi_usage.adjust, admit=pi_usage.admit, record=pi_usage.record)
        operations.update({'task.preview':task_runs.preview,'task.start':task_runs.start,'task.status':task_runs.status,
            'task.guard':task_runs.inference_guard,'task.review-checkpoint':task_runs.remember_review,'task.phase':task_runs.advance,'task.stop':task_runs.halt,
            'task.resume-preview':task_runs.resume_preview,'task.resume':task_runs.resume,'task.correct':task_runs.correct,
            'task.completion-preview':task_runs.completion_preview,'task.complete':task_runs.complete,
            'task.recovery-preview':task_runs.completion_recovery_preview,'task.recover':task_runs.recover_completion})
        operations.update({'review.context':review.context,'review.request':review.request,'review.admit':review.admit})
        operations.update({'engineering.preview':engineering_workflows.preview,'engineering.apply':engineering_workflows.apply})
        operations.update({'bootstrap.preview':project_bootstrap.preview,'bootstrap.apply':project_bootstrap.apply})
        operations.update({'scaffold.preview':scaffold_generation.preview,'scaffold.apply':scaffold_generation.apply,
                           'scaffold.cancel':scaffold_generation.cancel,'scaffold.inspect':scaffold_generation.inspect,'scaffold.status':scaffold_generation.status})
        operations.update({'infra-validation.preview':infra_validation.preview,'infra-validation.apply':infra_validation.apply,'infra-validation.cancel':infra_validation.cancel})
        operations.update({'documentation.catalog':documentation.catalog,'documentation.preview':documentation.preview,'documentation.apply':documentation.apply})
        operations.update({'documentation.recovery-preview':documentation_recovery.preview,'documentation.recover':documentation_recovery.apply})
        operations.update({'batch.recovery-preview':batch_recovery.preview,'batch.recover':batch_recovery.apply})
        operations.update({'workflow.answers-preview':workflows.answers_preview})
        operations.update({'workflow.choices':workflows.choices,'workflow.preview':workflows.preview,'workflow.apply':workflows.apply,'workflow.bind':task_binding.bind})
        operations.update({'migration.preview':migration_v8.preview,'migration.apply':migration_v8.apply,
                           'migration.rollback-preview':migration_v8.rollback_preview,'migration.rollback':migration_v8.rollback})
        operations.update({'checks.snapshot-preview':checks.preview_snapshot,'checks.snapshot':checks.apply_snapshot,
                           'checks.run-preview':checks.preview_run,'checks.run':checks.execute_host,'checks.cancel':check_cancel.request,
                           'checks.iteration-preview':checks.iteration_preview,'checks.iteration':checks.execute_iteration,
                           'checks.status':checks.status,'checks.refresh-preview':checks.refresh_preview,'checks.recovery-preview':checks.recovery_preview,
                           'checks.recover':checks.recover,'checks.review-preview':checks.review_preview})
        operations.update({'skills.manage-preview':skill_management.preview,'skills.manage-apply':skill_management.apply,
                           'skills.manage-status':skill_management.status,'skills.source-resolve':skill_management.resolve,
                           'skills.fetch-preview':skill_fetch.preview,'skills.fetch':skill_fetch.apply,
                           'skills.change-preview':selected_skills.change_preview})
        operations.update({'skills.preview':selected_skills.preview,'skills.apply':selected_skills.apply,
                           'skills.status':selected_skills.status,'skills.resolve':selected_skills.resolve,'skills.verify':selected_skills.verify})
        operations.update({'odd.preview':odd_workflow.preview,'odd.apply':odd_workflow.apply,'odd.status':odd_workflow.status})
        operations.update({'diagnostics.doctor':diagnostics.doctor,'diagnostics.quality':diagnostics.quality})
        operations.update({'memory.event':maintenance.session_event})
        operations.update({'sdd.preview':sdd.preview,'sdd.apply':sdd.apply,'sdd.status':sdd.status})
        if request['action'] not in operations: raise ValueError('Unknown host operation')
        # This process belongs to the trusted host. Repository metadata is never consent.
        result = operations[request['action']](root, **request['arguments'])
        reply = dict(ok=True, project=str(root), result=result)
    except (ValueError, TypeError, OSError, RecursionError):
        reply = dict(ok=False, project=str(root), error='runtime_state_unavailable')
    output=json.dumps(reply,ensure_ascii=True)
    if len(output.encode('utf8'))>65535:
        output=json.dumps(dict(ok=False,project=str(root),error='runtime_response_too_large'))
    print(output); return 0


if __name__ == '__main__': raise SystemExit(main())
