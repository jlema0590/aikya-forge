#!/usr/bin/env python3
"""Validador básico sin dependencias de la estructura Agent Skills.

No sustituye `skills-ref validate` oficial; chequea el subset usado por Forge.
"""
from __future__ import annotations
from aikya.resource_paths import project_root
import argparse
import json
import re
from pathlib import Path

NAME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def metadata_fields(front: str) -> dict[str,str]:
    """Bounded scalar subset; never resolve YAML aliases, tags or executable metadata."""
    if len(front.encode('utf8'))>16000:raise ValueError('Metadata exceeds its read bound')
    groups={};current=None
    for line in front.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        match=re.fullmatch(r'([a-z][a-z0-9-]*):[ \t]*(.*)',line)
        if match:
            current=match[1]
            if current in groups:raise ValueError('Duplicate metadata field')
            groups[current]=[match[2]]
        elif line[:1].isspace() and current is not None:groups[current].append(line.strip())
        else:raise ValueError('Unsupported skill metadata structure')
    fields={}
    for key,parts in groups.items():
        first=parts[0].strip()
        if first in ('>','>-','>+','|','|-','|+'):value=('\n' if first.startswith('|') else ' ').join(parts[1:]).strip()
        else:value=' '.join(part.strip() for part in parts).strip()
        if value.startswith('"'):
            try:value=json.loads(value)
            except ValueError as error:raise ValueError('Unsupported quoted metadata') from error
            if not isinstance(value,str):raise ValueError('Skill metadata must be scalar text')
        elif value.startswith("'"):
            if not value.endswith("'") or len(value)<2:raise ValueError('Unclosed metadata scalar')
            value=value[1:-1].replace("''","'")
        else:
            if key in ('name','description','compatibility') and value.startswith(('&','*','!')):
                raise ValueError('Metadata aliases and tags are not supported')
            value=value.split(' #',1)[0].rstrip()
        fields[key]=value
    return fields


def inspect_text(txt: str, directory_name: str, label: str='SKILL.md') -> list[str]:
    """Inspect bounded captured metadata without opening or executing a source file."""
    issues=[];path=label
    if not txt.startswith('---\n'):
        return [f'{path}: falta YAML frontmatter al inicio']
    parts = txt.split('---\n',2)
    if len(parts) < 3:
        return [f'{path}: frontmatter sin cierre']
    head = parts[1]
    try:fields=metadata_fields(head)
    except ValueError:return [f'{path}: metadata de skill no compatible']
    name, desc=fields.get('name',''),fields.get('description','')
    if not NAME.fullmatch(name) or not 1 <= len(name) <= 64 or name != directory_name:
        issues.append(f'{path}: name inválido o no coincide con directorio')
    if not 1 <= len(desc) <= 1024:
        issues.append(f'{path}: description ausente o fuera de rango')
    if 'compatibility' in fields and len(fields['compatibility'])>500:
        issues.append(f'{path}: compatibility >500 caracteres')
    if len(parts[2].splitlines()) > 500:
        issues.append(f'{path}: SKILL.md tiene >500 líneas, mueve detalles a references/')
    if not parts[2].strip():
        issues.append(f'{path}: instrucciones vacías')
    return issues



def inspect_skill(path: Path) -> list[str]:
    try:txt=path.read_text(encoding='utf8')
    except (UnicodeError,OSError):return [f'{path}: no se pudo leer SKILL.md']
    return inspect_text(txt,path.parent.name,str(path))


def validate(root: Path, include_vendor: bool = False) -> list[str]:
    base = root/'.claude/skills'
    if not base.exists():
        return [f'{base}: no existe directorio de skills']
    errors=[]
    skills=[s for s in base.iterdir() if s.is_dir()]
    if not skills:
        return [f'{base}: no hay skills']
    for skill in sorted(skills):
        if not include_vendor and skill.name in ('ponytail','graphify','ui-ux-pro-max'):
            continue  # externos se validan por su cadena de suministro upstream
        errors += inspect_skill(skill/'SKILL.md')
    return errors


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=project_root())
    parser.add_argument('--include-vendor',action='store_true')
    args=parser.parse_args()
    errors=validate(args.root.resolve(),args.include_vendor)
    print('\n'.join(errors) if errors else 'Skills locales: formato Agent Skills válido (comprobaciones básicas).')
    return bool(errors)

if __name__=='__main__':
    raise SystemExit(main())
