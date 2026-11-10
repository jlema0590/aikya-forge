"""Inert skill paths apply the shared portable policy and project secret exclusions."""
from aikya.code_index.policy import excluded
from aikya.core.package_paths import DEVICES,validate as members


def validate(paths,*,max_files=80,max_nodes=160):
    return members(paths,max_files=max_files,max_nodes=max_nodes,max_length=160,denied=excluded)
