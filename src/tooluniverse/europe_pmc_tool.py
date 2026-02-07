import requests
from .base_tool import BaseTool
from .tool_registry import register_tool
from .http_utils import request_with_retry
import xml.etree.ElementTree as ET
import re


@register_tool("EuropePMCTool")
class EuropePMCTool(BaseTool):
    """
    Tool to search for articles on Europe PMC including abstracts.
    """

    def __init__(
        self,
        tool_config,
        base_url="https://www.ebi.ac.uk/europepmc/webservices/rest/search",
    ):
        super().__init__(tool_config)
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def run(self, arguments):
        query = arguments.get("query")
        limit = arguments.get("limit", 5)
        enrich_missing_abstract = bool(arguments.get("enrich_missing_abstract", False))
        extract_terms_from_fulltext = arguments.get("extract_terms_from_fulltext")
        if not query:
            return [
                {
                    "title": "Error",
                    "abstract": None,
                    "authors": [],
                    "journal": None,
                    "year": None,
                    "doi": None,
                    "doi_url": None,
                    "url": None,
                    "citations": 0,
                    "open_access": False,
                    "keywords": [],
                    "source": "Europe PMC",
                    "error": "`query` parameter is required.",
                    "retryable": False,
                }
            ]
        return self._search(
            query,
            limit,
            enrich_missing_abstract=enrich_missing_abstract,
            extract_terms_from_fulltext=extract_terms_from_fulltext,
        )

    def _local_name(self, tag: str) -> str:
        return tag.rsplit("}", 1)[-1] if "}" in tag else tag

    def _extract_abstract_from_fulltext_xml(self, xml_text: str) -> str | None:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return None

        for el in root.iter():
            if self._local_name(el.tag).lower() == "abstract":
                text = " ".join("".join(el.itertext()).split())
                if text:
                    return text
        return None

    def _build_fulltext_xml_url(
        self, *, source_db: str | None, article_id: str | None, pmcid: str | None
    ) -> str | None:
        if pmcid:
            return (
                f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
            )
        if source_db and article_id:
            return f"https://www.ebi.ac.uk/europepmc/webservices/rest/{source_db}/{article_id}/fullTextXML"
        return None

    def _search(
        self,
        query,
        limit,
        *,
        enrich_missing_abstract: bool = False,
        extract_terms_from_fulltext: list | None = None,
    ):
        # First try core mode to get abstracts
        core_params = {
            "query": query,
            "resultType": "core",
            "pageSize": limit,
            "format": "json",
        }
        core_response = request_with_retry(
            self.session,
            "GET",
            self.base_url,
            params=core_params,
            timeout=20,
            max_attempts=3,
        )

        # Then try lite mode to get journal information
        lite_params = {
            "query": query,
            "resultType": "lite",
            "pageSize": limit,
            "format": "json",
        }
        lite_response = request_with_retry(
            self.session,
            "GET",
            self.base_url,
            params=lite_params,
            timeout=20,
            max_attempts=3,
        )

        if core_response.status_code != 200:
            return [
                {
                    "title": "Error",
                    "abstract": None,
                    "authors": [],
                    "journal": None,
                    "year": None,
                    "doi": None,
                    "url": None,
                    "citations": 0,
                    "open_access": False,
                    "keywords": [],
                    "source": "Europe PMC",
                    "error": f"Europe PMC API error {core_response.status_code}",
                    "reason": core_response.reason,
                    "retryable": core_response.status_code
                    in (408, 429, 500, 502, 503, 504),
                }
            ]

        # Get core mode results
        try:
            core_payload = core_response.json()
        except ValueError:
            return [
                {
                    "title": "Error",
                    "abstract": None,
                    "authors": [],
                    "journal": None,
                    "year": None,
                    "doi": None,
                    "url": None,
                    "citations": 0,
                    "open_access": False,
                    "keywords": [],
                    "source": "Europe PMC",
                    "error": "Europe PMC returned invalid JSON",
                    "retryable": True,
                }
            ]

        core_results = core_payload.get("resultList", {}).get("result", [])
        lite_results = []

        # If lite mode also succeeds, get journal information
        if lite_response.status_code == 200:
            try:
                lite_payload = lite_response.json()
            except ValueError:
                lite_payload = {}
            lite_results = lite_payload.get("resultList", {}).get("result", [])

        # Create ID to record mapping
        lite_map = {rec.get("id"): rec for rec in lite_results}

        articles = []
        for rec in core_results:
            # Extract basic information
            title = rec.get("title")
            abstract = rec.get("abstractText") or None
            year = rec.get("pubYear")

            # Extract author information
            authors = []
            author_list = rec.get("authorList", {}).get("author", [])
            if isinstance(author_list, list):
                for author in author_list:
                    if isinstance(author, dict):
                        full_name = author.get("fullName", "")
                        if full_name:
                            authors.append(full_name)
            elif isinstance(author_list, dict):
                full_name = author_list.get("fullName", "")
                if full_name:
                    authors.append(full_name)

            # Get journal information from lite mode
            journal = None
            if rec.get("id") in lite_map:
                lite_rec = lite_map[rec["id"]]
                journal = lite_rec.get("journalTitle")

            # If still no journal information, use source field
            if not journal:
                journal = rec.get("source")

            # Extract DOI
            doi = rec.get("doi") or None
            doi_url = f"https://doi.org/{doi}" if doi else None

            source_db = rec.get("source") or None
            article_id = rec.get("id") or None
            pmid = rec.get("pmid") or None
            pmcid = rec.get("pmcid") or None

            if isinstance(pmcid, str):
                pmcid = pmcid.strip() or None

            # Extract citation count
            citations = rec.get("citedByCount", 0)
            if citations:
                try:
                    citations = int(citations)
                except (ValueError, TypeError):
                    citations = 0

            # Extract open access status
            open_access_raw = rec.get("isOpenAccess", False)
            # Normalize to boolean (API can return 'Y'/'N' or True/False)
            if isinstance(open_access_raw, str):
                open_access = open_access_raw.upper() == "Y"
            else:
                open_access = bool(open_access_raw)

            # Extract keywords
            keywords = []
            text_mined_terms = rec.get("hasTextMinedTerms", {})
            if text_mined_terms and isinstance(text_mined_terms, dict):
                # Try to extract keywords
                for _key, value in text_mined_terms.items():
                    if isinstance(value, list):
                        keywords.extend(value)
                    elif isinstance(value, str):
                        keywords.append(value)

            # Build URL
            url = (
                f"https://europepmc.org/article/{source_db}/{article_id}"
                if source_db and article_id
                else None
            )
            fulltext_xml_url = self._build_fulltext_xml_url(
                source_db=source_db, article_id=article_id, pmcid=pmcid
            )

            articles.append(
                {
                    "title": title or "Title not available",
                    "abstract": abstract,
                    "authors": authors,
                    "journal": journal or None,
                    "year": year,
                    "doi": doi,
                    "url": url,
                    "source_db": source_db,
                    "article_id": article_id,
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "doi_url": doi_url,
                    "fulltext_xml_url": fulltext_xml_url,
                    "citations": citations,
                    "open_access": open_access,
                    "keywords": keywords,
                    "source": "Europe PMC",
                    "data_quality": {
                        "has_abstract": bool(abstract),
                        "has_authors": bool(authors),
                        "has_journal": bool(journal),
                        "has_year": bool(year),
                        "has_doi": bool(doi),
                        "has_citations": bool(citations and citations > 0),
                        "has_keywords": bool(keywords),
                        "has_url": bool(url),
                    },
                }
            )

        if enrich_missing_abstract:
            # Keep enrichment bounded to avoid slow calls.
            max_enrich = min(int(limit) if limit else 5, 3)
            enriched = 0
            for a in articles:
                if enriched >= max_enrich:
                    break
                if not isinstance(a, dict):
                    continue
                if a.get("abstract"):
                    continue
                fulltext_url = a.get("fulltext_xml_url")
                if not isinstance(fulltext_url, str) or not fulltext_url:
                    continue
                resp = request_with_retry(
                    self.session,
                    "GET",
                    fulltext_url,
                    timeout=20,
                    max_attempts=2,
                )
                if resp.status_code != 200:
                    continue
                abstract_from_fulltext = self._extract_abstract_from_fulltext_xml(
                    resp.text
                )
                if abstract_from_fulltext:
                    a["abstract"] = abstract_from_fulltext
                    a["abstract_source"] = "Europe PMC fullTextXML"
                    if isinstance(a.get("data_quality"), dict):
                        a["data_quality"]["has_abstract"] = True
                    enriched += 1

        # Extract fulltext snippets if requested
        if extract_terms_from_fulltext and isinstance(
            extract_terms_from_fulltext, list
        ):
            # Filter valid terms (max 5)
            valid_terms = [
                t.strip()
                for t in extract_terms_from_fulltext
                if isinstance(t, str) and t.strip()
            ][:5]

            if valid_terms:
                # Process up to 3 OA articles to avoid latency
                max_snippet_articles = 3
                processed = 0

                for a in articles:
                    if processed >= max_snippet_articles:
                        break
                    if not isinstance(a, dict):
                        continue
                    # Only process open access articles with fulltext URLs
                    if not a.get("open_access"):
                        continue
                    fulltext_url = a.get("fulltext_xml_url")
                    if not isinstance(fulltext_url, str) or not fulltext_url:
                        continue

                    # Extract snippets using the existing tool logic
                    try:
                        resp = request_with_retry(
                            self.session,
                            "GET",
                            fulltext_url,
                            timeout=30,
                            max_attempts=2,
                        )
                        if resp.status_code != 200:
                            continue

                        # Extract text from XML
                        try:
                            root = ET.fromstring(resp.text or "")
                            text = " ".join("".join(root.itertext()).split())
                        except ET.ParseError:
                            continue

                        # Extract snippets around terms
                        snippets = []
                        total_chars = 0
                        max_total_chars = 8000
                        window_chars = 220
                        max_snippets_per_term = 3
                        low = text.lower()

                        for term in valid_terms:
                            needle = term.lower()
                            found = 0
                            for m in re.finditer(re.escape(needle), low):
                                if found >= max_snippets_per_term:
                                    break
                                start = max(0, m.start() - window_chars)
                                end = min(len(text), m.end() + window_chars)
                                snippet = text[start:end].strip()
                                if total_chars + len(snippet) > max_total_chars:
                                    break
                                snippets.append({"term": term, "snippet": snippet})
                                total_chars += len(snippet)
                                found += 1

                        if snippets:
                            a["fulltext_snippets"] = snippets
                            a["fulltext_snippets_count"] = len(snippets)

                        processed += 1
                    except Exception:
                        # Silently skip articles that fail snippet extraction
                        continue

        return articles


@register_tool("EuropePMCFullTextSnippetsTool")
class EuropePMCFullTextSnippetsTool(BaseTool):
    """
    Fetch Europe PMC fullTextXML (open access) and return bounded text snippets
    around user-provided terms. This helps answer questions where the crucial
    detail is present in the full text (e.g., methods/section titles) but not
    necessarily in the abstract.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/xml, text/xml;q=0.9, */*;q=0.8"}
        )

    def _build_fulltext_xml_url(self, arguments: dict) -> str | None:
        fulltext_xml_url = arguments.get("fulltext_xml_url")
        if isinstance(fulltext_xml_url, str) and fulltext_xml_url.strip():
            return fulltext_xml_url.strip()

        pmcid = arguments.get("pmcid")
        if isinstance(pmcid, str) and pmcid.strip():
            pmcid = pmcid.strip()
            pmcid = pmcid if pmcid.upper().startswith("PMC") else f"PMC{pmcid}"
            return (
                f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
            )

        source_db = arguments.get("source_db") or arguments.get("source")
        article_id = arguments.get("article_id")
        if (
            isinstance(source_db, str)
            and source_db.strip()
            and isinstance(article_id, str)
            and article_id.strip()
        ):
            return f"https://www.ebi.ac.uk/europepmc/webservices/rest/{source_db.strip()}/{article_id.strip()}/fullTextXML"

        return None

    def _extract_text(self, xml_text: str) -> str:
        root = ET.fromstring(xml_text)
        # Collapse whitespace to make snippets readable and stable.
        return " ".join("".join(root.itertext()).split())

    def run(self, arguments):
        fulltext_url = self._build_fulltext_xml_url(arguments)
        terms = arguments.get("terms")

        if not fulltext_url:
            return {
                "status": "error",
                "error": "Provide `fulltext_xml_url`, or `pmcid`, or (`source_db` + `article_id`).",
                "retryable": False,
            }
        if not isinstance(terms, list) or not [
            t for t in terms if isinstance(t, str) and t.strip()
        ]:
            return {
                "status": "error",
                "error": "`terms` must be a non-empty list of strings.",
                "retryable": False,
            }

        try:
            window_chars = int(arguments.get("window_chars", 220))
        except (TypeError, ValueError):
            window_chars = 220
        window_chars = max(20, min(window_chars, 2000))

        try:
            max_snippets_per_term = int(arguments.get("max_snippets_per_term", 3))
        except (TypeError, ValueError):
            max_snippets_per_term = 3
        max_snippets_per_term = max(1, min(max_snippets_per_term, 10))

        try:
            max_total_chars = int(arguments.get("max_total_chars", 8000))
        except (TypeError, ValueError):
            max_total_chars = 8000
        max_total_chars = max(1000, min(max_total_chars, 50000))

        resp = request_with_retry(
            self.session, "GET", fulltext_url, timeout=30, max_attempts=3
        )
        if resp.status_code != 200:
            return {
                "status": "error",
                "error": f"Europe PMC fullTextXML fetch failed (HTTP {resp.status_code})",
                "url": getattr(resp, "url", fulltext_url),
                "status_code": resp.status_code,
                "retryable": resp.status_code in (408, 429, 500, 502, 503, 504),
            }

        try:
            text = self._extract_text(resp.text or "")
        except ET.ParseError:
            return {
                "status": "error",
                "error": "Europe PMC fullTextXML returned invalid XML",
                "url": getattr(resp, "url", fulltext_url),
                "retryable": True,
            }

        snippets = []
        total_chars = 0
        low = text.lower()

        for raw_term in terms:
            if not isinstance(raw_term, str):
                continue
            term = raw_term.strip()
            if not term:
                continue

            needle = term.lower()
            found = 0
            for m in re.finditer(re.escape(needle), low):
                if found >= max_snippets_per_term:
                    break
                start = max(0, m.start() - window_chars)
                end = min(len(text), m.end() + window_chars)
                snippet = text[start:end].strip()
                # Bound total output size
                if total_chars + len(snippet) > max_total_chars:
                    break
                snippets.append({"term": term, "snippet": snippet})
                total_chars += len(snippet)
                found += 1

        return {
            "status": "success",
            "url": getattr(resp, "url", fulltext_url),
            "snippets": snippets,
            "snippets_count": len(snippets),
            "truncated": total_chars >= max_total_chars,
        }


@register_tool("EuropePMCRESTTool")
class EuropePMCRESTTool(BaseTool):
    """
    Generic REST tool for Europe PMC API endpoints.
    Supports citations, references, and other article-related endpoints.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest"
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.timeout = 30

    def _build_url(self, arguments):
        """Build URL from endpoint template and arguments."""
        endpoint = self.tool_config["fields"]["endpoint"]
        url = endpoint
        for key, value in arguments.items():
            placeholder = f"{{{key}}}"
            if placeholder in url:
                url = url.replace(placeholder, str(value))
        return url

    def run(self, arguments):
        """Execute the Europe PMC REST API request."""
        try:
            url = self._build_url(arguments)

            # Extract query parameters (those not in URL path)
            params = {"format": "json"}
            endpoint_template = self.tool_config["fields"]["endpoint"]

            # Add parameters that are not path parameters
            for key, value in arguments.items():
                placeholder = f"{{{key}}}"
                if placeholder not in endpoint_template and value is not None:
                    # Europe PMC expects pageSize, not page_size.
                    if key == "page_size":
                        params["pageSize"] = value
                    else:
                        params[key] = value

            response = request_with_retry(
                self.session,
                "GET",
                url,
                params=params,
                timeout=self.timeout,
                max_attempts=3,
            )

            if response.status_code == 200:
                data = response.json()
                return {"status": "success", "data": data, "url": response.url}
            else:
                return {
                    "status": "error",
                    "error": f"Europe PMC API returned status {response.status_code}",
                    "url": response.url,
                    "status_code": response.status_code,
                    "detail": response.text[:200] if response.text else None,
                }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Europe PMC API request failed: {str(e)}",
                "url": url if "url" in locals() else None,
            }
