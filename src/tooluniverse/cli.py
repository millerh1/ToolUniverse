"""
tu — ToolUniverse CLI

Human-friendly command-line interface covering the same functionality as the
compact mode available in the ToolUniverse MCP server.

Subcommands:
    list    List available tools (mirrors list_tools)
    grep    Search by text/regex pattern (mirrors grep_tools)
    info    Get tool details (mirrors get_tool_info)
    find    Find tools by natural-language query (mirrors find_tools)
    run     Execute a tool (mirrors execute_tool, same interface)
    test    Test a tool with example inputs and report pass/fail
    status  Show current ToolUniverse status
    build   Regenerate the static lazy registry
    serve   Start the MCP stdio server (same as `tooluniverse`)
"""

import contextlib
import json
import os
import sys
import argparse
from typing import Any

# Redirect ToolUniverse logger to stderr so JSON output on stdout stays clean.
# Set env var early so it takes effect even if logging_config is imported
# before _get_tu() is called (e.g., by pytest or other imports).
os.environ.setdefault("TOOLUNIVERSE_STDIO_MODE", "1")

# Skip the heavy MCP/fastmcp/http-client imports that tooluniverse/__init__.py
# pulls in unconditionally — the CLI never needs them (tu serve loads smcp
# explicitly inside cmd_serve).  This saves ~480 ms on every invocation.
# Users can opt out with: TOOLUNIVERSE_LIGHT_IMPORT=0 tu <command>
os.environ.setdefault("TOOLUNIVERSE_LIGHT_IMPORT", "1")

_TRUNC = 60  # max description chars in table output


def _get_tu():
    """Lazy-initialize a ToolUniverse instance."""
    # Reconfigure logger to stderr in case the singleton was already created
    # before our env var took effect (e.g., tooluniverse imported elsewhere).
    try:
        from tooluniverse.logging_config import reconfigure_for_stdio

        reconfigure_for_stdio()
    except Exception:
        pass

    from tooluniverse import ToolUniverse

    tu = ToolUniverse()
    if not tu.all_tool_dict:
        print("Loading tools…", end="", flush=True, file=sys.stderr)
        tu._auto_load_tools_if_empty()
        print(f" done ({len(tu.all_tools)} tools)", file=sys.stderr)
    return tu


@contextlib.contextmanager
def _status_to_stderr():
    """Route print() status messages to stderr so stdout stays pure JSON."""
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old_stdout


def _compact(d: dict) -> dict:
    """Remove keys whose value is None so optional params are truly omitted."""
    return {k: v for k, v in d.items() if v is not None}


# ── render functions ────────────────────────────────────────────────────────────


def _trunc(s: str, n: int = _TRUNC) -> str:
    """Truncate string to n chars, appending '…' if truncated."""
    if not s:
        return ""
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def _render_list(d: dict) -> str:
    """Render list_tools result as human-readable text."""
    lines = []

    # categories mode: two-column table sorted by count
    if "categories" in d and "total_tools" not in d:
        cats = d["categories"]
        sorted_cats = sorted(cats.items(), key=lambda x: -x[1])
        if not sorted_cats:
            return "(no categories)"
        col1 = max(len(k) for k, _ in sorted_cats)
        col1 = max(col1, 8)
        lines.append(f"{'category':<{col1}}  {'tools':>5}")
        lines.append("─" * (col1 + 8))
        for cat, cnt in sorted_cats:
            lines.append(f"{cat:<{col1}}  {cnt:>5}")
        total = sum(cats.values())
        lines.append(f"\n{len(cats)} categories · {total} tools")
        return "\n".join(lines)

    # names mode: plain list with summary
    tools = d.get("tools", [])
    if not tools:
        return f"(no tools)  total={d.get('total_tools', 0)}"
    if isinstance(tools[0], str):
        for name in tools:
            lines.append(name)
        total = d.get("total_tools", len(tools))
        has_more = d.get("has_more", False)
        more_hint = "  (use --offset to page)" if has_more else ""
        lines.append(f"\n{len(tools)} of {total} tools{more_hint}")
        return "\n".join(lines)

    # basic/summary/custom mode: name + optional description
    col1 = max((len(t.get("name", "")) for t in tools), default=8)
    col1 = max(col1, 8)
    if any("description" in t for t in tools):
        lines.append(f"{'name':<{col1}}  description")
        lines.append("─" * (col1 + 2 + _TRUNC))
        for t in tools:
            lines.append(f"{t.get('name',''):<{col1}}  {_trunc(t.get('description',''))}")
    else:
        for t in tools:
            lines.append(str(t))
    total = d.get("total_tools", len(tools))
    lines.append(f"\n{len(tools)} of {total} tools")
    return "\n".join(lines)


def _render_grep(d: dict) -> str:
    """Render grep_tools result as two-column name + description table."""
    if "error" in d:
        return f"Error: {d['error']}"
    tools = d.get("tools", [])
    total = d.get("total_matches", 0)
    if not tools:
        return f"0 of {total} matches"
    col1 = max((len(t.get("name", "")) for t in tools), default=8)
    col1 = max(col1, 8)
    lines = [f"{'name':<{col1}}  description", "─" * (col1 + 2 + _TRUNC)]
    for t in tools:
        lines.append(f"{t.get('name',''):<{col1}}  {_trunc(t.get('description',''))}")
    has_more = d.get("has_more", False)
    more_hint = "  (use --offset to page)" if has_more else ""
    lines.append(f"\n{len(tools)} of {total} matches{more_hint}")
    return "\n".join(lines)


def _render_find(d: dict) -> str:
    """Render find_tools result as score + name + description table."""
    if "error" in d:
        return f"Error: {d['error']}"
    tools = d.get("tools", [])
    if not tools:
        return "0 results"
    col1 = max((len(t.get("name", "")) for t in tools), default=8)
    col1 = max(col1, 8)
    lines = [f"{'score':>7}  {'name':<{col1}}  description", "─" * (7 + 2 + col1 + 2 + _TRUNC)]
    for t in tools:
        score = t.get("score", t.get("relevance_score", ""))
        if isinstance(score, float):
            score_str = f"{score:.3f}"
        else:
            score_str = str(score)
        lines.append(f"{score_str:>7}  {t.get('name',''):<{col1}}  {_trunc(t.get('description',''))}")
    lines.append(f"\n{len(tools)} results")
    return "\n".join(lines)


def _render_info(d: dict) -> str:
    """Render get_tool_info result as human-readable tool card."""
    # batch result
    if "tools" in d:
        parts = []
        for t in d["tools"]:
            parts.append(_render_info(t))
        return "\n\n".join(parts)

    name = d.get("name", "?")
    category = d.get("category", "")
    desc = d.get("description", "")
    cat_str = f"  [{category}]" if category else ""
    lines = [f"{name}{cat_str}", f"  {desc}"]

    params = d.get("parameter", {})
    if params and isinstance(params, dict):
        props = params.get("properties", {})
        required = set(params.get("required", []))
        if props:
            lines.append("\n  Parameters:")
            for pname, pdef in props.items():
                ptype = pdef.get("type", "")
                req = "required" if pname in required else ""
                pdesc = _trunc(pdef.get("description", ""), 50)
                req_str = f"  {req}" if req else ""
                lines.append(f"    {pname:<20} {ptype:<10}{req_str}  {pdesc}")
    return "\n".join(lines)


def _render_status(d: dict) -> str:
    """Render status as key-value pairs + top categories list."""
    lines = [
        f"tools loaded:    {d.get('tools_loaded', '?')}",
        f"categories:      {d.get('categories', '?')}",
        f"workspace:       {d.get('workspace', '?')}",
        f"profile active:  {'yes' if d.get('profile_active') else 'no'}",
    ]
    top = d.get("top_categories", {})
    if top:
        lines.append("\ntop categories:")
        for cat, cnt in top.items():
            lines.append(f"  {cat:<20} {cnt}")
    return "\n".join(lines)


# ── output helper ───────────────────────────────────────────────────────────────


def _print_result(result: Any, args: argparse.Namespace, render_fn=None) -> None:
    """Print result. Respects --raw / --json / human-readable default."""
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            print(result)
            return
    if args.raw:
        print(json.dumps(result, ensure_ascii=False))
    elif args.json or render_fn is None:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        try:
            print(render_fn(result))
        except Exception:
            print(json.dumps(result, indent=2, ensure_ascii=False))


# ── category helpers ────────────────────────────────────────────────────────────


def _resolve_categories(tu, names: list) -> list:
    """Map user-supplied names to actual stored category keys (case-insensitive)."""
    actual = set((tu.tool_category_dicts or {}).keys())
    lower_map = {k.lower(): k for k in actual}
    return [lower_map.get(n.lower(), n) for n in names]


# ── run argument parsing ────────────────────────────────────────────────────────


def _infer_type(s: str):
    """'10' → 10, 'true' → True, 'null' → None, else string."""
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() == "null":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _parse_run_args(argv: list) -> "dict | None":
    """Parse ['{"k":"v"}'] or ['k1=v1', 'k2=v2'] → dict, or [] → None."""
    if not argv:
        return None
    if len(argv) == 1:
        # Try JSON parse first for any single token (handles objects and arrays)
        try:
            return json.loads(argv[0])
        except json.JSONDecodeError:
            pass
        # Not JSON: fall through to key=value path
    # key=value path
    result = {}
    for token in argv:
        if "=" not in token:
            raise ValueError(f"Expected key=value, got: {token!r}")
        k, _, v = token.partition("=")
        k = k.strip()
        if not k:
            raise ValueError(f"Invalid argument: empty parameter name in {token!r}")
        result[k] = _infer_type(v)
    return result


# ── subcommand handlers ────────────────────────────────────────────────────────


def cmd_list(args: argparse.Namespace) -> None:
    # Determine mode: smart default when user didn't set it explicitly
    mode = args.mode
    if mode is None:
        mode = "names" if args.categories else "categories"

    with _status_to_stderr():
        tu = _get_tu()
        if args.categories:
            args.categories = _resolve_categories(tu, args.categories)
        result = tu.run_one_function(
            {
                "name": "list_tools",
                "arguments": _compact(
                    {
                        "mode": mode,
                        "categories": args.categories,
                        "fields": args.fields,
                        "limit": args.limit,
                        "offset": args.offset,
                        "group_by_category": args.group_by_category,
                    }
                ),
            }
        )
    _print_result(result, args, _render_list)


def cmd_grep(args: argparse.Namespace) -> None:
    with _status_to_stderr():
        tu = _get_tu()
        if args.categories:
            args.categories = _resolve_categories(tu, args.categories)
        result = tu.run_one_function(
            {
                "name": "grep_tools",
                "arguments": _compact(
                    {
                        "pattern": args.pattern,
                        "field": args.field,
                        "search_mode": args.search_mode,
                        "limit": args.limit,
                        "offset": args.offset,
                        "categories": args.categories,
                    }
                ),
            }
        )
    _print_result(result, args, _render_grep)


def cmd_info(args: argparse.Namespace) -> None:
    with _status_to_stderr():
        tu = _get_tu()
        # Pass a single string when only one tool is requested
        tool_names = args.tool_names[0] if len(args.tool_names) == 1 else args.tool_names
        result = tu.run_one_function(
            {
                "name": "get_tool_info",
                "arguments": {
                    "tool_names": tool_names,
                    "detail_level": args.detail,
                },
            }
        )
    _print_result(result, args, _render_info)


def cmd_find(args: argparse.Namespace) -> None:
    """Find tools with keyword-based search (no LLM/API keys required)."""
    with _status_to_stderr():
        tu = _get_tu()
        if args.categories:
            args.categories = _resolve_categories(tu, args.categories)
        from tooluniverse.tool_finder_keyword import ToolFinderKeyword

        finder = ToolFinderKeyword({}, tooluniverse=tu)
        raw_result = finder._run_json_search(
            _compact(
                {
                    "description": args.query,
                    "limit": args.limit,
                    "categories": args.categories,
                }
            )
        )
    try:
        result = json.loads(raw_result)
    except (json.JSONDecodeError, TypeError):
        result = {"raw": raw_result}
    _print_result(result, args, _render_find)


def cmd_run(args: argparse.Namespace) -> None:
    """Execute a tool.

    Interface mirrors execute_tool:
      tool_name  — name of the tool to run (required)
      arguments  — key=value pairs OR JSON string (optional)
    """
    arguments = None
    try:
        arguments = _parse_run_args(args.arguments)
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"Error: invalid arguments.\n  {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    with _status_to_stderr():
        tu = _get_tu()
        result = tu.run_one_function(
            {
                "name": "execute_tool",
                # Omit `arguments` key entirely when None so the tool sees its
                # own default rather than a None that fails JSON schema validation.
                "arguments": _compact(
                    {"tool_name": args.tool_name, "arguments": arguments}
                ),
            }
        )
    # cmd_run: always JSON output (result is tool-specific data, no render_fn)
    _print_result(result, args, render_fn=None)


def cmd_status(args: argparse.Namespace) -> None:
    with _status_to_stderr():
        tu = _get_tu()
        tu._auto_load_tools_if_empty()
        category_counts = {
            cat: len(tools) for cat, tools in (tu.tool_category_dicts or {}).items()
        }
    status = {
        "tools_loaded": len(tu.all_tools),
        "categories": len(category_counts),
        "workspace": str(tu._workspace_dir),
        "profile_active": tu._workspace_profile_config is not None,
        "top_categories": dict(
            sorted(category_counts.items(), key=lambda x: -x[1])[:10]
        ),
    }
    _print_result(status, args, _render_status)


def cmd_test(args: argparse.Namespace) -> None:
    """Test a tool against example inputs and report pass/fail."""
    import time

    use_color = sys.stderr.isatty() or sys.stdout.isatty()
    green  = "\033[32m" if use_color else ""
    red    = "\033[31m" if use_color else ""
    yellow = "\033[33m" if use_color else ""
    bold   = "\033[1m"  if use_color else ""
    reset  = "\033[0m"  if use_color else ""

    def _ok(msg):   return f"{green}✓{reset} {msg}"
    def _fail(msg): return f"{red}✗{reset} {msg}"
    def _warn(msg): return f"{yellow}!{reset} {msg}"

    # ── resolve test list ─────────────────────────────────────────────────────
    if args.config:
        import json as _json
        with open(args.config) as f:
            cfg = _json.load(f)
        tool_name = cfg["tool_name"]
        tests = [
            {
                "name": t.get("name", ""),
                "args": t["args"],
                "expect_status": t.get("expect_status"),
                "expect_keys": t.get("expect_keys", []),
            }
            for t in cfg.get("tests", [])
        ]
    else:
        tool_name = args.tool_name
        if args.args_json:
            import json as _json
            try:
                parsed = _json.loads(args.args_json)
            except _json.JSONDecodeError as exc:
                print(f"Error: invalid JSON arguments — {exc}", file=sys.stderr)
                sys.exit(1)
            tests = [{"name": "", "args": parsed, "expect_status": None, "expect_keys": []}]
        else:
            tests = None  # resolve from test_examples after loading

    # ── load ──────────────────────────────────────────────────────────────────
    with _status_to_stderr():
        tu = _get_tu()

    if tool_name not in tu.all_tool_dict:
        print(_fail(f"Tool '{tool_name}' not found. Run `tu list` to see available tools."))
        sys.exit(1)

    tool_def = tu.all_tool_dict[tool_name]

    # ── resolve test_examples if no tests provided ────────────────────────────
    if tests is None:
        examples = tool_def.get("test_examples", []) if isinstance(tool_def, dict) else []
        if not examples:
            print(_warn(
                f"No test_examples found for '{tool_name}' and no arguments given.\n"
                f"  Pass explicit args:  tu test {tool_name} '{{\"q\": \"test\"}}'\n"
                f"  Or add test_examples to the tool's JSON config."
            ))
            sys.exit(1)
        tests = [
            {"name": f"example {i+1}", "args": ex, "expect_status": None, "expect_keys": []}
            for i, ex in enumerate(examples)
        ]

    # ── run tests ─────────────────────────────────────────────────────────────
    import json as _json

    print(f"\n{bold}Testing: {tool_name}{reset}  ({len(tests)} test{'s' if len(tests) != 1 else ''})\n")
    passed = 0
    for t in tests:
        label = t["name"] or _json.dumps(t["args"])
        t0 = time.time()
        try:
            result = tu.run_one_function({"name": tool_name, "arguments": t["args"]})
        except Exception as exc:
            elapsed = time.time() - t0
            print(f"  {_fail(label)}  [{elapsed:.2f}s]")
            print(f"    Exception: {exc}")
            continue

        elapsed = time.time() - t0
        failures = []

        if t["expect_status"] and isinstance(result, dict):
            got = result.get("status")
            if got != t["expect_status"]:
                failures.append(f"status: expected '{t['expect_status']}', got '{got}'")

        for key in t["expect_keys"]:
            if isinstance(result, dict) and key not in result:
                failures.append(f"missing key '{key}' in result")

        if result is None:
            failures.append("result is None")
        elif isinstance(result, dict) and not result:
            failures.append("result is an empty dict")

        # return_schema validation (auto, from tool definition)
        if not failures and isinstance(result, dict) and result.get("status") == "success":
            return_schema = tool_def.get("return_schema") if isinstance(tool_def, dict) else None
            if return_schema:
                try:
                    import jsonschema
                    jsonschema.validate(result.get("data"), return_schema)
                except ImportError:
                    pass  # jsonschema not installed — skip silently
                except jsonschema.ValidationError as exc:
                    failures.append(f"return_schema mismatch: {exc.message} (at {list(exc.absolute_path)})")

        if failures:
            print(f"  {_fail(label)}  [{elapsed:.2f}s]")
            for f in failures:
                print(f"    {f}")
            print(f"    result: {_json.dumps(result, default=str)[:300]}")
        else:
            preview = _json.dumps(result, default=str)[:120]
            print(f"  {_ok(label)}  [{elapsed:.2f}s]  {preview}…")
            passed += 1

    # ── summary ───────────────────────────────────────────────────────────────
    failed = len(tests) - passed
    print(f"\n{'─' * 50}")
    if failed == 0:
        print(f"{green}{bold}All {len(tests)} test(s) passed.{reset}")
    else:
        print(f"{red}{bold}{failed}/{len(tests)} test(s) failed.{reset}")
        sys.exit(1)


def cmd_build(args: argparse.Namespace) -> None:
    """Regenerate the static lazy registry and coding-API wrapper files."""
    from pathlib import Path

    # Resolve output directory.
    # Default: .tooluniverse/coding_api/ next to the current workspace —
    # never touches the installed package in site-packages.
    output_dir = Path(args.output) if args.output else Path.cwd() / ".tooluniverse" / "coding_api"

    # Step 1 — lazy registry (always writes back into the installed package;
    # this is a small internal optimisation file and is harmless to update).
    try:
        print("Regenerating lazy registry…")
        mod = __import__("tooluniverse.generate_lazy_registry", fromlist=["main"])
        mod.main()
    except SystemExit as exc:
        if exc.code not in (None, 0):
            sys.exit(exc.code)
    except Exception as exc:
        print(f"Error in generate_lazy_registry: {exc}", file=sys.stderr)
        sys.exit(1)

    # Step 2 — coding-API wrappers → user-specified or local workspace dir.
    try:
        print("Regenerating coding-API wrappers…")
        mod = __import__("tooluniverse.generate_tools", fromlist=["main"])
        mod.main(output_dir=output_dir)
    except SystemExit as exc:
        if exc.code not in (None, 0):
            sys.exit(exc.code)
    except Exception as exc:
        print(f"Error in generate_tools: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_serve(_args: argparse.Namespace) -> None:
    """Start the MCP stdio server — identical to running `tooluniverse`."""
    from tooluniverse.smcp_server import run_default_stdio_server

    run_default_stdio_server()


# ── argument parser ────────────────────────────────────────────────────────────


def main() -> None:
    # Shared output flags
    _out = argparse.ArgumentParser(add_help=False)
    _out.add_argument(
        "--json",
        action="store_true",
        help="Output as pretty JSON",
    )
    _out.add_argument(
        "--raw",
        action="store_true",
        help="Output compact JSON (suitable for piping)",
    )

    parser = argparse.ArgumentParser(
        prog="tu",
        description="ToolUniverse CLI — discover and run scientific tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  tu list\n"
            "  tu list --categories uniprot\n"
            "  tu grep protein --field description\n"
            "  tu find 'protein structure analysis' --limit 5\n"
            "  tu info UniProt_get_entry_by_accession\n"
            "  tu run UniProt_get_entry_by_accession accession=P12345\n"
            '  tu run UniProt_get_entry_by_accession \'{"accession": "P12345"}\'\n'
            "  tu test Dryad_search_datasets\n"
            "  tu test MyAPI_search '{\"q\": \"test\"}'\n"
            "  tu status\n"
            "  tu build\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ── list ──────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "list",
        help="List available tools",
        parents=[_out],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  tu list\n"
            "  tu list --mode categories\n"
            "  tu list --categories ChEMBL UniProt --limit 20\n"
            "  tu list --mode by_category --group-by-category\n"
            "  tu list --mode custom --fields name type category\n"
        ),
    )
    p.add_argument(
        "--mode",
        default=None,
        choices=["names", "categories", "basic", "by_category", "summary", "custom"],
        help="Output mode (default: categories overview, or names when --categories given)",
    )
    p.add_argument(
        "--categories", nargs="+", metavar="CAT", help="Filter by category names"
    )
    p.add_argument(
        "--fields",
        nargs="+",
        metavar="FIELD",
        help="Fields to include (required for --mode custom, e.g. name type category)",
    )
    p.add_argument("--limit", type=int, default=None, help="Max tools to return")
    p.add_argument("--offset", type=int, default=0, help="Skip first N tools")
    p.add_argument(
        "--group-by-category",
        dest="group_by_category",
        action="store_true",
        help="Group results by category",
    )
    p.set_defaults(func=cmd_list)

    # ── grep ──────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "grep",
        help="Search tools by text or regex pattern",
        parents=[_out],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  tu grep protein\n"
            "  tu grep protein --field description\n"
            "  tu grep '^UniProt' --mode regex\n"
            "  tu grep drug --field description --limit 20\n"
        ),
    )
    p.add_argument("pattern", help="Search pattern")
    p.add_argument(
        "--field",
        default="name",
        choices=["name", "description", "type", "category"],
        help="Field to search in (default: name)",
    )
    p.add_argument(
        "--mode",
        dest="search_mode",
        default="text",
        choices=["text", "regex"],
        help="text = case-insensitive substring; regex = regular expression (default: text)",
    )
    p.add_argument("--limit", type=int, default=100, help="Max results (default: 100)")
    p.add_argument("--offset", type=int, default=0, help="Skip first N results")
    p.add_argument(
        "--categories", nargs="+", metavar="CAT", help="Filter by category names"
    )
    p.set_defaults(func=cmd_grep)

    # ── info ──────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "info",
        help="Get tool details",
        parents=[_out],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  tu info UniProt_get_entry_by_accession\n"
            "  tu info UniProt_get_entry_by_accession --detail description\n"
            "  tu info UniProt_get_entry_by_accession ChEMBL_get_molecule\n"
        ),
    )
    p.add_argument("tool_names", nargs="+", metavar="TOOL", help="Tool name(s)")
    p.add_argument(
        "--detail",
        default="full",
        choices=["description", "full"],
        help="'description' for summary only; 'full' for complete schema (default: full)",
    )
    p.set_defaults(func=cmd_info)

    # ── find ──────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "find",
        help="Find tools by natural-language query",
        parents=[_out],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  tu find 'protein structure analysis'\n"
            "  tu find 'search for drug targets' --limit 5\n"
            "  tu find 'gene expression' --categories GTEx ENCODE\n"
        ),
    )
    p.add_argument("query", help="Natural-language search query")
    p.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    p.add_argument(
        "--categories", nargs="+", metavar="CAT", help="Filter by category names"
    )
    p.set_defaults(func=cmd_find)

    # ── run ───────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "run",
        help="Execute a tool",
        parents=[_out],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Arguments can be key=value pairs or a single JSON string.\n\n"
            "Examples:\n"
            "  tu run UniProt_get_entry_by_accession accession=P12345\n"
            "  tu run list_tools mode=categories\n"
            '  tu run UniProt_get_entry_by_accession \'{"accession": "P12345"}\'\n'
            "  tu run grep_tools '{\"pattern\": \"protein\", \"field\": \"name\"}'\n"
        ),
    )
    p.add_argument("tool_name", help="Name of the tool to execute")
    p.add_argument(
        "arguments",
        nargs="*",
        default=[],
        metavar="ARG",
        help="Tool arguments: JSON string OR key=value pairs",
    )
    p.set_defaults(func=cmd_run)

    # ── test ──────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "test",
        help="Test a tool with example inputs and report pass/fail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  tu test Dryad_search_datasets              # uses test_examples from the tool's JSON config\n"
            "  tu test MyAPI_search '{\"q\": \"test\"}'  # single ad-hoc call\n"
            "  tu test --config my_tool_tests.json        # full config with assertions\n\n"
            "Config file format (my_tool_tests.json):\n"
            "  {\n"
            '    "tool_name": "MyAPI_search",\n'
            '    "tests": [\n'
            '      {"name": "basic", "args": {"q": "test"}, "expect_status": "success", "expect_keys": ["data"]}\n'
            "    ]\n"
            "  }\n"
        ),
    )
    p.add_argument("tool_name", nargs="?", help="Tool name to test")
    p.add_argument("args_json", nargs="?", metavar="ARGS", help="JSON arguments for a single ad-hoc test")
    p.add_argument("--config", "-c", metavar="FILE", help="Path to a JSON test config file")
    p.set_defaults(func=cmd_test)

    # ── status ────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "status",
        help="Show ToolUniverse status",
        parents=[_out],
    )
    p.set_defaults(func=cmd_status)

    # ── build ─────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "build",
        help="Rebuild the static tool registry (run after adding new built-in tools)",
    )
    p.add_argument(
        "--output",
        metavar="DIR",
        default=None,
        help=(
            "Directory to write coding-API wrapper files into "
            "(default: .tooluniverse/coding_api/)"
        ),
    )
    p.set_defaults(func=cmd_build)

    # ── serve ─────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "serve",
        help="Start the MCP stdio server (identical to `tooluniverse`)",
    )
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
