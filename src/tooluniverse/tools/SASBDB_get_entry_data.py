"""
SASBDB_get_entry_data

Retrieve comprehensive metadata and experimental conditions for a specific SASBDB entry. Returns ...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def SASBDB_get_entry_data(
    sasbdb_id: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Optional[dict[str, Any]]:
    """
    Retrieve comprehensive metadata and experimental conditions for a specific SASBDB entry. Returns ...

    Parameters
    ----------
    sasbdb_id : str
        SASBDB entry identifier (e.g., 'SASDBA2', 'SASDBW5', 'SASDP92'). Find IDs via...
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    Optional[dict[str, Any]]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {"name": "SASBDB_get_entry_data", "arguments": {"sasbdb_id": sasbdb_id}},
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["SASBDB_get_entry_data"]
