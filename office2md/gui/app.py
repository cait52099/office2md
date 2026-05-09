from __future__ import annotations

from pathlib import Path

import streamlit as st

from office2md.gui.helpers import (
    is_valid_library_path,
    load_library_overview,
    normalize_library_path,
    overview_metrics,
    run_library_search,
)


def main() -> None:
    st.set_page_config(page_title="office2md GUI MVP", layout="wide")
    st.title("office2md GUI MVP")

    st.sidebar.header("Library")
    library_value = st.sidebar.text_input("Library path", value="")
    library_path = normalize_library_path(library_value)

    page = st.sidebar.radio(
        "Page",
        [
            "Library Overview",
            "Search",
            "Locate Document",
            "Evidence Package",
            "Runner Dry-run",
        ],
    )

    if page == "Library Overview":
        render_library_overview(library_path)
    elif page == "Search":
        render_search(library_path)
    elif page == "Locate Document":
        render_placeholder("Locate Document", "Locate-document panel is planned for v0.3.0 P3.")
    elif page == "Evidence Package":
        render_placeholder("Evidence Package", "Evidence package controls are planned for v0.3.0 P4.")
    elif page == "Runner Dry-run":
        render_placeholder("Runner Dry-run", "Runner dry-run controls are planned for v0.3.0 P5.")


def render_library_overview(library_path: Path | None) -> None:
    st.header("Library Overview")
    if not is_valid_library_path(library_path):
        st.warning("Enter a valid Knowledge Library folder or library.db path in the sidebar.")
        return

    try:
        report = load_library_overview(library_path)
    except Exception as exc:  # pragma: no cover - Streamlit UI guard.
        st.error(f"Unable to load library report: {exc}")
        return

    metrics = overview_metrics(report)
    columns = st.columns(3)
    for index, (label, value) in enumerate(metrics.items()):
        columns[index % 3].metric(label, value)

    st.subheader("Document Kind Distribution")
    st.dataframe(_dict_rows(report.get("document_kind_distribution", {})), hide_index=True, use_container_width=True)

    st.subheader("Chunks Without Locator")
    st.json(
        {
            "total": report.get("chunks_without_locator", 0),
            "by_document_kind": report.get("chunks_without_locator_by_document_kind", {}),
            "by_evidence_type": report.get("chunks_without_locator_by_evidence_type", {}),
            "by_extension": report.get("chunks_without_locator_by_extension", {}),
            "top_sources": report.get("chunks_without_locator_top_sources", [])[:5],
        }
    )


def render_search(library_path: Path | None) -> None:
    st.header("Search")
    if not is_valid_library_path(library_path):
        st.warning("Enter a valid Knowledge Library folder or library.db path in the sidebar.")
        return

    query = st.text_input("Query", value="")
    control_columns = st.columns(4)
    limit = int(control_columns[0].number_input("Limit", min_value=1, max_value=100, value=5, step=1))
    diagnostics = control_columns[1].checkbox("Diagnostics", value=False)
    facets = control_columns[2].checkbox("Facets", value=False)
    context = int(control_columns[3].number_input("Context", min_value=0, max_value=20, value=0, step=1))

    filter_columns = st.columns(2)
    output_dir = filter_columns[0].text_input("Output dir filter", value="")
    entity = filter_columns[1].text_input("Entity filter", value="")

    if not query.strip():
        st.info("Enter a search query to view results.")
        return

    try:
        search_data = run_library_search(
            library_path,
            query,
            limit=limit,
            diagnostics=diagnostics,
            facets=facets,
            context=context,
            output_dir=output_dir,
            entity=entity,
        )
    except Exception as exc:  # pragma: no cover - Streamlit UI guard.
        st.error(f"Unable to run search: {exc}")
        return

    results = search_data["results"]
    if not results:
        st.info("No results found.")
        return

    st.subheader("Results")
    st.dataframe(search_data["rows"], hide_index=True, use_container_width=True)
    st.download_button(
        "Download search JSON",
        data=search_data["export_json"],
        file_name="office2md_search_results.json",
        mime="application/json",
    )

    if diagnostics:
        render_search_diagnostics(search_data["diagnostics"])
    if facets:
        render_search_facets(search_data["facets"])
    if context > 0:
        render_related_chunks(results)


def render_search_diagnostics(diagnostics: dict) -> None:
    st.subheader("Diagnostics")
    st.json(
        {
            "mode": diagnostics.get("mode"),
            "effective_query": diagnostics.get("effective_query"),
            "alias_used": diagnostics.get("alias_used"),
            "normalized_query": diagnostics.get("normalized_query"),
            "token_fallback_used": diagnostics.get("token_fallback_used"),
            "fallback_tokens": diagnostics.get("fallback_tokens"),
            "result_count": diagnostics.get("result_count"),
            "shown_count": diagnostics.get("shown_count"),
            "locator_coverage": diagnostics.get("locator_coverage"),
            "hints": diagnostics.get("hints"),
        }
    )


def render_search_facets(facets: dict) -> None:
    st.subheader("Facets")
    for name in ["document_kind", "evidence_type", "source_file", "output_dir"]:
        rows = facets.get(name) or []
        if rows:
            st.caption(name)
            st.dataframe(rows, hide_index=True, use_container_width=True)


def render_related_chunks(results: list[dict]) -> None:
    rows = []
    for item in results:
        for related in item.get("related_chunks", []):
            rows.append(
                {
                    "result_rank": item.get("rank"),
                    "chunk_id": related.get("chunk_id"),
                    "evidence_type": related.get("evidence_type"),
                    "locator": related.get("locator"),
                    "preview": related.get("preview"),
                }
            )
    if rows:
        st.subheader("Related Chunks")
        st.dataframe(rows, hide_index=True, use_container_width=True)


def render_placeholder(title: str, body: str) -> None:
    st.header(title)
    st.info(body)


def _dict_rows(values: dict) -> list[dict]:
    return [{"name": key, "count": value} for key, value in values.items()]


if __name__ == "__main__":
    main()
