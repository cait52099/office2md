from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from office2md.gui.helpers import (
    build_library_command_preview,
    build_runner_command_preview,
    graph_json_path,
    graph_node_types,
    graph_summary,
    graph_view_html,
    is_valid_library_path,
    load_curated_concept_index,
    load_library_overview,
    load_library_graph,
    normalize_library_path,
    overview_metrics,
    prepare_curated_knowledge_graph,
    prepare_document_concept_graph,
    prepare_raw_provenance_graph,
    run_library_search,
    scan_source_folder_for_gui,
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
            "Graph View",
            "Build / Update Library",
            "Locate Document",
            "Evidence Package",
            "Runner Dry-run",
        ],
    )

    if page == "Library Overview":
        render_library_overview(library_path)
    elif page == "Search":
        render_search(library_path)
    elif page == "Graph View":
        render_graph_view(library_path)
    elif page == "Build / Update Library":
        render_build_update_library()
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


def render_graph_view(library_path: Path | None) -> None:
    st.header("Graph View")
    if library_path is None:
        st.warning("Enter a valid Knowledge Library folder or library.db path in the sidebar.")
        return

    graph_path = graph_json_path(library_path)
    if not graph_path.exists():
        st.warning(f"library_graph.json was not found at {graph_path}.")
        return

    try:
        graph = load_library_graph(library_path)
    except Exception as exc:  # pragma: no cover - Streamlit UI guard.
        st.error(f"Unable to load library graph: {exc}")
        return

    summary = graph_summary(graph)
    metric_columns = st.columns(2)
    metric_columns[0].metric("node_count", summary["node_count"])
    metric_columns[1].metric("edge_count", summary["edge_count"])

    st.subheader("Graph Summary")
    summary_columns = st.columns(2)
    summary_columns[0].dataframe(_dict_rows(summary["node_type_distribution"]), hide_index=True, use_container_width=True)
    summary_columns[1].dataframe(_dict_rows(summary["edge_type_distribution"]), hide_index=True, use_container_width=True)

    graph_mode = st.selectbox(
        "Graph mode",
        ["Curated Knowledge Graph", "Document-Concept Graph", "Raw Provenance Graph"],
    )
    if graph_mode == "Raw Provenance Graph":
        st.info(
            "Debug view: may include chunks, assets, source pages, and low-level edge types."
        )
    elif graph_mode == "Curated Knowledge Graph":
        st.info(
            "This view filters raw entities and source/provenance nodes to show higher-value domain concepts."
        )

    node_types = ["All", *graph_node_types(graph)]
    if graph_mode == "Raw Provenance Graph":
        control_columns = st.columns(5)
        max_nodes = int(control_columns[0].number_input("Max nodes", min_value=10, max_value=500, value=150, step=10))
        selected_type = control_columns[1].selectbox("Node type", node_types)
        keyword = control_columns[2].text_input("Keyword filter", value="")
        show_isolated = control_columns[3].checkbox("Show isolated nodes", value=True)
        show_edge_labels = control_columns[4].checkbox("Show edge labels", value=False)
        graph_view = prepare_raw_provenance_graph(
            graph,
            max_nodes=max_nodes,
            node_type=None if selected_type == "All" else selected_type,
            keyword=keyword,
            show_isolated=show_isolated,
        )
    else:
        control_columns = st.columns(4)
        default_max_nodes = 50 if graph_mode == "Curated Knowledge Graph" else 80
        max_nodes = int(control_columns[0].number_input("Max nodes", min_value=10, max_value=500, value=default_max_nodes, step=10))
        keyword = control_columns[1].text_input("Keyword filter", value="")
        show_isolated = control_columns[2].checkbox("Show isolated nodes", value=True)
        show_edge_labels = control_columns[3].checkbox("Show edge labels", value=False)
        concept_index = load_curated_concept_index(library_path)
        graph_view = (
            prepare_curated_knowledge_graph(concept_index, max_nodes=max_nodes, keyword=keyword, show_isolated=show_isolated)
            if graph_mode == "Curated Knowledge Graph"
            else prepare_document_concept_graph(concept_index, max_nodes=max_nodes, keyword=keyword, show_isolated=show_isolated)
        )
        st.caption(f"Concept filter applied. Hidden noisy concept labels: {concept_index['hidden_noisy_concepts_count']}.")
    st.caption(f"Rendering {len(graph_view['nodes'])} nodes and {len(graph_view['edges'])} edges from {graph_path}.")

    if graph_view["nodes"]:
        try:
            components.html(graph_view_html(graph_view, show_edge_labels=show_edge_labels), height=680, scrolling=True)
        except Exception as exc:  # pragma: no cover - optional pyvis/browser rendering guard.
            st.warning(f"Interactive graph rendering is unavailable: {exc}")
            render_graph_fallback(graph_view)
    else:
        st.info("No graph nodes matched the current filters. Try a broader term, try Raw Provenance Graph, or confirm the term exists in the library.")
        render_graph_fallback(graph_view)


def render_graph_fallback(graph_view: dict) -> None:
    st.subheader("Graph Data")
    if graph_view.get("node_rows"):
        st.caption("Nodes")
        st.dataframe(graph_view["node_rows"], hide_index=True, use_container_width=True)
    if graph_view.get("edge_rows"):
        st.caption("Edges")
        st.dataframe(graph_view["edge_rows"], hide_index=True, use_container_width=True)


def render_build_update_library() -> None:
    st.header("Build / Update Library")
    st.caption("Scan / Dry-run only. This page does not convert files or build a library.")

    path_columns = st.columns(2)
    source_value = path_columns[0].text_input("Source folder", value="")
    conversion_output_value = path_columns[1].text_input("Conversion output folder", value="")
    library_output_value = path_columns[0].text_input("Library output folder", value="")
    log_value = path_columns[1].text_input("Log folder", value="")

    option_columns = st.columns(4)
    max_files_value = option_columns[0].text_input("Max files", value="3")
    full_directory = option_columns[1].checkbox("Full directory", value=False)
    skip_existing = option_columns[2].checkbox("Skip existing", value=True)
    render_pdf_pages = option_columns[3].checkbox("Render PDF pages", value=True)

    page_columns = st.columns(2)
    max_render_pages = int(page_columns[0].number_input("Max render pages", min_value=1, max_value=100, value=3, step=1))
    max_text_pages = int(page_columns[1].number_input("Max text pages", min_value=1, max_value=1000, value=10, step=1))

    st.info(
        "Validated defaults: no OCR and no AI. The dry-run reads filesystem metadata only and does not create, "
        "delete, convert, or build anything."
    )
    if not skip_existing:
        st.warning("The validated runner workflow skips existing manifests; changing this is not implemented in the GUI dry-run.")
    if not render_pdf_pages or max_render_pages != 3 or max_text_pages != 10:
        st.warning(
            "The current PowerShell runner preview uses the validated render defaults. Custom render settings are "
            "shown for planning but are not executed by this dry-run page."
        )

    if not st.button("Scan / Dry-run"):
        return

    try:
        source_folder = _required_path(source_value, "Source folder")
        conversion_output_folder = _required_path(conversion_output_value, "Conversion output folder")
        library_output_folder = _required_path(library_output_value, "Library output folder")
        log_folder = _required_path(log_value, "Log folder")
        max_files = _parse_optional_int(max_files_value)
        if not full_directory and max_files is None:
            st.error("Enter Max files or enable Full directory before scanning.")
            return
        dry_run = scan_source_folder_for_gui(
            source_folder,
            conversion_output_folder,
            max_files=max_files,
            full_directory=full_directory,
        )
    except Exception as exc:  # pragma: no cover - Streamlit UI guard.
        st.error(f"Unable to run dry-run scan: {exc}")
        return

    render_dry_run_summary(dry_run)

    st.subheader("Recommended Next Commands")
    st.caption("Preview only. The GUI does not execute these commands in P4-B.")
    st.code(
        build_runner_command_preview(
            source_folder,
            conversion_output_folder,
            log_folder,
            max_files=max_files,
            full_directory=full_directory,
        ),
        language="powershell",
    )
    st.code(build_library_command_preview(conversion_output_folder, library_output_folder), language="powershell")


def render_dry_run_summary(dry_run: dict) -> None:
    metric_columns = st.columns(4)
    metric_columns[0].metric("supported_files", dry_run["supported_files_count"])
    metric_columns[1].metric("selected_target_files", dry_run["selected_files_count"])
    metric_columns[2].metric("expected_unique_manifests", dry_run["expected_unique_manifest_count"])
    metric_columns[3].metric("existing_manifests", dry_run["existing_manifest_count"])

    status_columns = st.columns(3)
    status_columns[0].metric("completed_expected_manifests", dry_run["completed_expected_manifest_count"])
    status_columns[1].metric("failed_manifests", dry_run["failed_manifest_count"])
    status_columns[2].metric("target_reached", "yes" if dry_run["target_reached"] else "no")

    if dry_run.get("warnings"):
        st.subheader("Warnings")
        for warning in dry_run["warnings"]:
            st.warning(warning)


def render_placeholder(title: str, body: str) -> None:
    st.header(title)
    st.info(body)


def _dict_rows(values: dict) -> list[dict]:
    return [{"name": key, "count": value} for key, value in values.items()]


def _required_path(value: str, label: str) -> Path:
    cleaned = (value or "").strip().strip('"')
    if not cleaned:
        raise ValueError(f"{label} is required.")
    return Path(cleaned).expanduser()


def _parse_optional_int(value: str) -> int | None:
    text = (value or "").strip()
    if not text:
        return None
    parsed = int(text)
    if parsed < 1:
        raise ValueError("Max files must be a positive integer.")
    return parsed


if __name__ == "__main__":
    main()
