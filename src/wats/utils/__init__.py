"""
Package shim for wats.utils: delegate implementation to the internal
`legacy` submodule. This avoids name conflicts between a top-level
`utils.py` module and the `utils` package when bundling with tools like
PyInstaller.
"""

from .legacy import *  # noqa: F401,F403

__all__ = [
    name
    for name in (
        "create_connection_filter_frame",
        "create_user_filter_frame",
        "create_group_filter_frame",
        "FilterableTreeFrame",
        "hash_password_md5",
        "parse_particularities",
    )
    if name in globals()
]