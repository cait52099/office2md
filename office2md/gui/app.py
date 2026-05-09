from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from office2md.gui.helpers import (
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


def render_placeholder(title: str, body: str) -> None:
    st.header(title)
    st.info(body)


def _dict_rows(values: dict) -> list[dict]:
    return [{"name": key, "count": value} for key, value in values.items()]


if __name__ == "__main__":
    main()
