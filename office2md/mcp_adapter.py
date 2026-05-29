from pathlib import Path
from typing import Any

from office2md.kb_gateway import kb_context as gateway_kb_context
from office2md.kb_gateway import kb_list as gateway_kb_list
from office2md.kb_gateway import kb_review as gateway_kb_review
from office2md.utils import utc_now_iso


MCP_ERROR_SCHEMA_VERSION = "office2md.mcp_error.v1"


def kb_list(catalog_path: str) -> dict[str, Any]:
    """Return registered libraries from an office2md library catalog."""
    try:
        return gateway_kb_list(Path(catalog_path))
    except (OSError, ValueError) as exc:
        return _error_payload("kb_list", str(exc))


def kb_context(
    catalog_path: str,
    query: str,
    library_id: str | None = None,
    library_ids: list[str] | None = None,
    libraries: str | None = None,
    limit: int = 5,
    context: int = 1,
) -> dict[str, Any]:
    """Return one read-only agent context packet from registered libraries."""
    try:
        selected_library_ids = _parse_library_ids(library_id=library_id, library_ids=library_ids, libraries=libraries)
        return gateway_kb_context(
            Path(catalog_path),
            query,
            library_ids=selected_library_ids,
            limit=limit,
            context=context,
        )
    except (OSError, ValueError) as exc:
        return _error_payload("kb_context", str(exc), query=query)


def kb_review(catalog_path: str, library_id: str) -> dict[str, Any]:
    """Return read-only update readiness review for one registered library."""
    try:
        return gateway_kb_review(Path(catalog_path), library_id)
    except (OSError, ValueError) as exc:
        return _error_payload("kb_review", str(exc), library_id=library_id)


def build_server() -> Any:
    """Build an optional FastMCP server exposing only read-only gateway tools."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("The optional 'mcp' package is required to run the office2md MCP adapter.") from exc

    server = FastMCP("office2md")
    server.tool(name="kb_list")(kb_list)
    server.tool(name="kb_context")(kb_context)
    server.tool(name="kb_review")(kb_review)
    return server


def main() -> None:
    build_server().run()


def _parse_library_ids(
    *,
    library_id: str | None = None,
    library_ids: list[str] | None = None,
    libraries: str | None = None,
) -> list[str] | None:
    values: list[str] = []
    if library_id:
        values.append(library_id)
    for item in library_ids or []:
        if item:
            values.append(item)
    if libraries:
        values.extend(item.strip() for item in libraries.split(",") if item.strip())
    return values or None


def _error_payload(tool: str, message: str, **request: Any) -> dict[str, Any]:
    return {
        "schema_version": MCP_ERROR_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "tool": tool,
        "request": request,
        "error": {"message": message},
        "warnings": [message],
        "limitations": [
            "office2md MCP adapter is read-only",
            "adapter exposes gateway tools only and does not expose unrestricted SQL or shell execution",
        ],
    }


if __name__ == "__main__":
    main()
