"""
EuropePMC_search_articles

Search for articles on Europe PMC including abstracts. The tool queries the Europe PMC web servic...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def EuropePMC_search_articles(
    query: str,
    limit: Optional[int] = 5,
    enrich_missing_abstract: Optional[bool] = False,
    extract_terms_from_fulltext: Optional[list[str]] = None,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> list[Any]:
    """
    Search for articles on Europe PMC including abstracts. The tool queries the Europe PMC web servic...

    Parameters
    ----------
    query : str
        Search query for Europe PMC. Use keywords separated by spaces to refine your ...
    limit : int
        Number of articles to return. This sets the maximum number of articles retrie...
    enrich_missing_abstract : bool
        If true, best-effort fills missing abstracts by fetching Europe PMC fullTextX...
    extract_terms_from_fulltext : list[str]
        Optional list of terms to extract from full text (open access only). When pro...
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    list[Any]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {
            "name": "EuropePMC_search_articles",
            "arguments": {
                "query": query,
                "limit": limit,
                "enrich_missing_abstract": enrich_missing_abstract,
                "extract_terms_from_fulltext": extract_terms_from_fulltext,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["EuropePMC_search_articles"]
