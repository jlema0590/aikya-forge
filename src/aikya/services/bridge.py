"""Bounded JSON bridge with read services and host-granted writes. No SDK or shell."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

MAX_REQUEST = 16_384
MAX_RESPONSE = 65_536
MAX_PROFILE = 100_000
OPERATIONS = ("capabilities", "status", "context")


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate field")
        result[key] = value
    return result


def profile_status(root: Path) -> dict:
    path = root / ".harness" / "project-profile.json"
    if (root / ".harness").is_symlink() or path.is_symlink():
        raise ValueError("Unsafe profile")
    if not path.exists():
        return dict(configured=False, methodology=None, project_type=None)
    if not path.is_file():
        raise ValueError("Profile must be a regular file")
    with path.open("rb") as stream:
        raw = stream.read(MAX_PROFILE + 1)
    if len(raw) > MAX_PROFILE:
        raise ValueError("Oversized profile")
    profile = json.loads(raw, object_pairs_hook=unique_fields)
    if not isinstance(profile, dict):
        raise ValueError("Invalid profile")
    profile = profile.get("decisions", profile)
    if not isinstance(profile, dict):
        raise ValueError("Invalid decisions")
    mode = profile.get("methodology")
    kind = profile.get("project_type")
    if mode not in (None, "odd", "sdd") or kind not in (
            None, "development", "infrastructure", "devops"):
        raise ValueError("Unknown profile values")
    return dict(configured=True, methodology=mode, project_type=kind)


def scoped_context(root: Path, arguments: dict) -> dict:
    from aikya.context.prepare import prepare_context
    from aikya.code_index.policy import excluded
    from aikya.core.checkpoints import safe_file
    if set(arguments) != {"query", "paths", "max_chars"}:
        raise ValueError("Invalid context arguments")
    paths, query, budget = arguments["paths"], arguments["query"], arguments["max_chars"]
    if not isinstance(query, str) or len(query) > 1000:
        raise ValueError("Invalid query")
    if (not isinstance(paths, list) or not 1 <= len(paths) <= 20
            or any(not isinstance(p, str) for p in paths) or len(set(paths)) != len(paths)):
        raise ValueError("Explicit unique paths required")
    if type(budget) is not int or not 512 <= budget <= 6000:
        raise ValueError("Invalid packet budget")
    if any(path.startswith('@skill/') for path in paths):
        if len(paths)!=1:raise ValueError('Select one approved skill resource')
        match=re.fullmatch(r'@skill/([a-z0-9]+(?:-[a-z0-9]+)*)/([^#]+)(?:#([0-9]{1,7}))?',paths[0])
        if not match:raise ValueError('Invalid approved skill resource alias')
        from .selected_skills import read_resource
        return read_resource(root,match[1],match[2],offset=int(match[3] or 0),max_chars=budget)
    for path in paths:
        safe_file(root, path)
        if excluded(path):
            raise ValueError("Excluded context path")
    return prepare_context(root, query, paths=paths, max_chars=budget, refresh_index=False)


def dispatch(root: Path, request: object) -> dict:
    """Validate every boundary independently of the TypeScript client."""
    ident = None
    try:
        if not isinstance(request, dict):
            raise ValueError("Object required")
        raw_id = request.get("id")
        if isinstance(raw_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", raw_id):
            ident = raw_id
        if set(request) != {"schema", "id", "project", "operation", "arguments"}:
            raise ValueError("Unknown fields")
        if type(request["schema"]) is not int or request["schema"] != 1 or ident is None:
            raise ValueError("Invalid envelope")
        arguments = request["arguments"]
        if request["project"] != str(root) or not isinstance(arguments, dict):
            raise ValueError("Invalid scope or arguments")
        operation = request["operation"]
        if not isinstance(operation, str) or operation not in (*OPERATIONS, 'write-preview', 'write', 'batch-preview', 'batch', 'memory-status', 'memory-search'):
            raise ValueError("Unknown operation")
        if operation in ('batch-preview','batch'):
            from . import source_batches
            if operation=='batch-preview':
                if set(arguments)!={'intent','session'}:raise ValueError('Batch preview requires explicit intent/session')
                result=source_batches.preview(root,arguments['intent'],session=arguments['session'])
            else:
                if set(arguments)!={'session','intent','grant'}:raise ValueError('Invalid source batch request')
                result=source_batches.apply(root,arguments['session'],arguments['intent'],arguments['grant'],
                                             bytes.fromhex(os.environ.get('AIKYA_HOST_KEY','')))
        elif operation in ('memory-status', 'memory-search'):
            from . import memory
            if operation == 'memory-status':
                if arguments: raise ValueError('Unexpected memory status arguments')
                result = memory.status(root)
            else:
                if set(arguments) != {'query', 'max_chars'}: raise ValueError('Invalid memory query')
                result = memory.search(root, **arguments)
        elif operation == 'write-preview':
            from .authorization import preview
            if set(arguments)!={'intent','session'}: raise ValueError('Write preview requires a session')
            result = preview(root, arguments['intent'], session=arguments['session'])
        elif operation == 'write':
            from .authorization import apply_write
            if set(arguments) != {'session', 'intent', 'grant'}: raise ValueError('Invalid write request')
            result = apply_write(root, arguments['session'], arguments['intent'], arguments['grant'],
                                 bytes.fromhex(os.environ.get('AIKYA_HOST_KEY', '')))
        elif operation == "context":
            result = scoped_context(root, arguments)
        else:
            if arguments:
                raise ValueError("Unexpected arguments")
            result = (dict(operations=list(OPERATIONS), writes=False, model_execution=False)
                      if operation == "capabilities" else profile_status(root))
        return dict(schema=1, id=ident, project=str(root), ok=True, result=result)
    except (ValueError, OSError, TypeError, UnicodeError, RecursionError):
        # Never echo profile contents, paths from malformed input, or exception text.
        return dict(schema=1, id=ident, project=str(root), ok=False, error="invalid_request")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve(strict=True)
    if not root.is_dir():
        parser.error("Project must be a directory")
    raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
    try:
        if len(raw) > MAX_REQUEST:
            raise ValueError("Oversized request")
        request = json.loads(raw, object_pairs_hook=unique_fields)
    except (ValueError, UnicodeError, RecursionError):
        request = None
    response = json.dumps(dispatch(root, request), ensure_ascii=True)
    if len(response.encode()) > MAX_RESPONSE:
        return 2
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
