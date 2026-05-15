from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from office2md.gui.helpers import (
    build_obsidian_export_command_preview,
    build_library_command_preview,
    build_runner_command_preview,
    derive_workspace_paths,
    graph_json_path,
    graph_node_types,
    graph_summary,
    graph_view_html,
    is_conversion_output_path,
    is_valid_library_path,
    load_curated_concept_index,
    load_library_overview,
    load_library_graph,
    normalize_library_path,
    overview_metrics,
    prepare_curated_knowledge_graph,
    prepare_document_concept_graph,
    prepare_raw_provenance_graph,
    run_build_library_command,
    run_obsidian_export_for_gui,
    run_library_search,
    run_convert_update_command,
    scan_source_folder_for_gui,
    summarize_library_output,
    summarize_obsidian_export_output,
    suggest_workspace_path,
    validate_workspace_paths,
    workspace_warnings,
)


def main() -> None:
    st.set_page_config(page_title="office2md GUI MVP", layout="wide")
    st.title("office2md GUI MVP")

    st.sidebar.header("Library")
    pending_library_path = st.session_state.pop("pending_library_path_value", None)
    if pending_library_path is not None:
        st.session_state["library_path_value"] = pending_library_path
    if "library_path_value" not in st.session_state:
        st.session_state["library_path_value"] = ""
    library_value = st.sidebar.text_input("Library path", key="library_path_value")
    library_path = normalize_library_path(library_value)

    page = st.sidebar.radio(
        "Page",
        [
            "Library Overview",
            "Search",
            "Graph View",
            "Build / Update Library",
            "Export",
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
    elif page == "Export":
        render_export(library_path)
    elif page == "Locate Document":
        render_placeholder("Locate Document", "Locate-document panel is planned for v0.3.0 P3.")
    elif page == "Evidence Package":
        render_placeholder("Evidence Package", "Evidence package controls are planned for v0.3.0 P4.")
    elif page == "Runner Dry-run":
        render_placeholder("Runner Dry-run", "Runner dry-run controls are planned for v0.3.0 P5.")


def render_library_overview(library_path: Path | None) -> None:
    st.header("Library Overview")
    if not is_valid_library_path(library_path):
        if is_conversion_output_path(library_path):
            st.warning("This looks like a conversion output folder, not a built library. Load the workspace library folder instead.")
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
        if is_conversion_output_path(library_path):
            st.warning("This looks like a conversion output folder, not a built library. Load the workspace library folder instead.")
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
    if is_conversion_output_path(library_path):
        st.warning("This looks like a conversion output folder, not a built library. Load the workspace library folder instead.")
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
        ["Knowledge Graph", "Document-Concept Graph", "Raw Provenance Graph"],
    )
    if graph_mode == "Raw Provenance Graph":
        st.info(
            "Debug view: may include chunks, assets, source pages, and low-level edge types."
        )
    elif graph_mode == "Knowledge Graph":
        st.info(
            "This library-native view detects concepts from the current library content. It does not apply a fixed equipment vocabulary."
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
        default_max_nodes = 50 if graph_mode == "Knowledge Graph" else 80
        max_nodes = int(control_columns[0].number_input("Max nodes", min_value=10, max_value=500, value=default_max_nodes, step=10))
        keyword = control_columns[1].text_input("Keyword filter", value="")
        show_isolated = control_columns[2].checkbox("Show isolated nodes", value=True)
        show_edge_labels = control_columns[3].checkbox("Show edge labels", value=False)
        concept_index = load_curated_concept_index(library_path)
        graph_view = (
            prepare_curated_knowledge_graph(concept_index, max_nodes=max_nodes, keyword=keyword, show_isolated=show_isolated)
            if graph_mode == "Knowledge Graph"
            else prepare_document_concept_graph(concept_index, max_nodes=max_nodes, keyword=keyword, show_isolated=show_isolated)
        )
        st.caption(
            "Library-native concept extraction applied. Low-confidence text fragments are filtered from the Knowledge Graph. "
            f"Hidden noisy concept labels: {concept_index['hidden_noisy_concepts_count']}."
        )
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
    st.caption("Select a source folder and one output workspace. The GUI keeps conversion, library, and logs separate.")

    path_columns = st.columns(2)
    source_value = path_columns[0].text_input("Source Folder: original documents", value="")
    source_preview = normalize_library_path(source_value)
    suggested_workspace = suggest_workspace_path(source_preview)
    workspace_default = str(suggested_workspace) if suggested_workspace else ""
    workspace_value = path_columns[1].text_input("Output Workspace Folder", value=workspace_default)

    option_columns = st.columns(4)
    max_files_value = option_columns[0].text_input("Max files", value="3")
    full_directory = option_columns[1].checkbox("Full directory", value=False)
    skip_existing = option_columns[2].checkbox("Skip existing", value=True)
    render_pdf_pages = option_columns[3].checkbox("Render PDF pages", value=True)

    page_columns = st.columns(2)
    max_render_pages = int(page_columns[0].number_input("Max render pages", min_value=1, max_value=100, value=3, step=1))
    max_text_pages = int(page_columns[1].number_input("Max text pages", min_value=1, max_value=1000, value=10, step=1))
    runner_columns = st.columns(2)
    timeout_minutes = int(runner_columns[0].number_input("Timeout minutes", min_value=1, max_value=1440, value=45, step=1))
    max_attempts = int(runner_columns[1].number_input("Max attempts", min_value=1, max_value=100, value=20, step=1))

    st.info(
        "The workspace folder keeps conversion outputs, the final library, and logs separate. Load Built Library uses "
        "the workspace\\library folder. Validated defaults: no OCR and no AI."
    )
    if not skip_existing:
        st.warning("The validated runner workflow skips existing manifests; changing this is not implemented in the GUI dry-run.")
    if not render_pdf_pages or max_render_pages != 3 or max_text_pages != 10:
        st.warning(
            "The current PowerShell runner preview uses the validated render defaults. Custom render settings are "
            "shown for planning but are not passed to the current runner command."
        )

    try:
        source_folder = _required_path(source_value, "Source folder")
        workspace_folder = _required_path(workspace_value, "Output Workspace Folder")
        validate_workspace_paths(source_folder, workspace_folder)
        workspace_paths = derive_workspace_paths(workspace_folder)
        conversion_output_folder = workspace_paths["conversion_output_folder"]
        library_output_folder = workspace_paths["library_output_folder"]
        log_folder = workspace_paths["log_folder"]
        max_files = _parse_optional_int(max_files_value)
        if not full_directory and max_files is None:
            raise ValueError("Enter Max files or enable Full directory before scanning or converting.")
        runner_command = build_runner_command_preview(
            source_folder,
            conversion_output_folder,
            log_folder,
            max_files=max_files,
            full_directory=full_directory,
            timeout_minutes=timeout_minutes,
            max_attempts=max_attempts,
        )
        build_command = build_library_command_preview(conversion_output_folder, library_output_folder)
    except Exception as exc:
        st.error(f"Review the Build / Update Library inputs: {exc}")
        return

    st.subheader("Derived Workspace Paths")
    st.info(
        "The Conversion Output Folder is not directly readable as a Library. Run Build Library first, then load the "
        "Library Output Folder."
    )
    derived_columns = st.columns(3)
    derived_columns[0].write({"Conversion Output Folder": str(conversion_output_folder), "purpose": "per-document Knowledge Pack outputs"})
    derived_columns[1].write({"Library Output Folder": str(library_output_folder), "purpose": "final searchable library with library.db"})
    derived_columns[2].write({"Log Folder": str(log_folder), "purpose": "runner logs"})
    for warning in workspace_warnings(workspace_folder):
        st.warning(warning)

    st.subheader("Scan / Dry-run")
    if st.button("Scan / Dry-run"):
        try:
            dry_run = scan_source_folder_for_gui(
                source_folder,
                conversion_output_folder,
                max_files=max_files,
                full_directory=full_directory,
            )
        except Exception as exc:  # pragma: no cover - Streamlit UI guard.
            st.error(f"Unable to run dry-run scan: {exc}")
        else:
            render_dry_run_summary(dry_run)

    st.subheader("Recommended Next Commands")
    st.caption("Preview commands. Build Library is shown for later use and is not executed by Convert / Update.")
    st.code(runner_command, language="powershell")
    st.code(build_command, language="powershell")

    render_convert_update_section(
        source_folder,
        conversion_output_folder,
        log_folder,
        max_files=max_files,
        full_directory=full_directory,
        timeout_minutes=timeout_minutes,
        max_attempts=max_attempts,
        runner_command=runner_command,
        skip_existing=skip_existing,
        render_pdf_pages=render_pdf_pages,
        max_render_pages=max_render_pages,
        max_text_pages=max_text_pages,
    )

    render_build_library_section(conversion_output_folder, library_output_folder, build_command)


def render_export(library_path: Path | None) -> None:
    st.header("Export")
    st.subheader("Export to Obsidian Vault")
    st.info(
        "Obsidian does not need to be installed for export. The output folder can later be opened as an Obsidian vault. "
        "Assets are not copied in this MVP. Concept extraction is heuristic and library-native, so real-use tuning may still be needed."
    )

    library_default = str(library_path) if library_path is not None else ""
    input_columns = st.columns(2)
    library_value = input_columns[0].text_input("Current Library Path", value=library_default)
    vault_value = input_columns[1].text_input("Obsidian Vault Output Folder", value="")

    option_columns = st.columns(4)
    max_concepts = int(option_columns[0].number_input("Max Concepts", min_value=0, max_value=10000, value=100, step=10))
    max_evidence = int(option_columns[1].number_input("Max Evidence Per Concept", min_value=0, max_value=100, value=5, step=1))
    overwrite = option_columns[2].checkbox("Overwrite existing output", value=False)
    dry_run = option_columns[3].checkbox("Dry-run", value=False)

    try:
        selected_library = _required_path(library_value, "Current Library Path")
        vault_output = _required_path(vault_value, "Obsidian Vault Output Folder")
        preview_command = build_obsidian_export_command_preview(
            selected_library,
            vault_output,
            overwrite=overwrite,
            dry_run=dry_run,
            max_concepts=max_concepts,
            max_evidence_per_concept=max_evidence,
        )
    except Exception as exc:
        st.error(f"Review the Export inputs: {exc}")
        return

    st.subheader("Command Preview")
    st.code(preview_command, language="powershell")

    button_columns = st.columns(2)
    if button_columns[0].button("Preview Export"):
        try:
            preview = run_obsidian_export_for_gui(
                selected_library,
                vault_output,
                overwrite=overwrite,
                dry_run=True,
                max_concepts=max_concepts,
                max_evidence_per_concept=max_evidence,
            )
        except Exception as exc:  # pragma: no cover - Streamlit UI guard.
            st.error(f"Unable to preview export: {exc}")
        else:
            render_obsidian_export_result(preview, dry_run=True)

    if button_columns[1].button("Export to Obsidian"):
        try:
            result = run_obsidian_export_for_gui(
                selected_library,
                vault_output,
                overwrite=overwrite,
                dry_run=dry_run,
                max_concepts=max_concepts,
                max_evidence_per_concept=max_evidence,
            )
        except Exception as exc:  # pragma: no cover - Streamlit UI guard.
            st.error(f"Obsidian export failed: {exc}")
        else:
            render_obsidian_export_result(result, dry_run=dry_run)
            if not dry_run:
                render_obsidian_export_summary(vault_output)


def render_obsidian_export_result(result: dict, dry_run: bool) -> None:
    title = "Export Preview" if dry_run else "Export Result"
    st.subheader(title)
    metrics = st.columns(3)
    metrics[0].metric("documents_exported", result.get("documents_exported", 0))
    metrics[1].metric("concepts_exported", result.get("concepts_exported", 0))
    metrics[2].metric("warnings", len(result.get("warnings") or []))
    st.write({"vault_output": result.get("vault_output"), "dry_run": result.get("options", {}).get("dry_run")})
    st.subheader("Generated Structure")
    st.code(
        "\n".join(
            [
                "00_Index.md",
                "00_Library_Report.md",
                "Documents/",
                "Concepts/",
                "_office2md/export_manifest.json",
            ]
        ),
        language="text",
    )
    for warning in result.get("warnings") or []:
        st.warning(warning)


def render_obsidian_export_summary(vault_output: Path) -> None:
    summary = summarize_obsidian_export_output(vault_output)
    st.subheader("Export Manifest Summary")
    st.write({key: value for key, value in summary.items() if key != "manifest"})
    if summary.get("manifest"):
        st.json(summary["manifest"])


def render_convert_update_section(
    source_folder: Path,
    conversion_output_folder: Path,
    log_folder: Path,
    max_files: int | None,
    full_directory: bool,
    timeout_minutes: int,
    max_attempts: int,
    runner_command: str,
    skip_existing: bool,
    render_pdf_pages: bool,
    max_render_pages: int,
    max_text_pages: int,
) -> None:
    st.subheader("Convert / Update")
    st.warning(
        "This runs the existing PowerShell chunked conversion runner. Streamlit may be busy until the command exits. "
        "Use a small MaxFiles test before FullDirectory."
    )
    detail_columns = st.columns(2)
    detail_columns[0].write(
        {
            "source_folder": str(source_folder),
            "conversion_output_folder": str(conversion_output_folder),
            "mode": "FullDirectory" if full_directory else "MaxFiles",
            "max_files": None if full_directory else max_files,
            "skip_existing": skip_existing,
            "no_ocr": True,
            "no_ai": True,
        }
    )
    detail_columns[1].write(
        {
            "log_folder": str(log_folder),
            "timeout_minutes": timeout_minutes,
            "max_attempts": max_attempts,
            "render_pdf_pages": render_pdf_pages,
            "max_render_pages": max_render_pages,
            "max_text_pages": max_text_pages,
        }
    )
    st.code(runner_command, language="powershell")
    confirmed = st.checkbox("I understand this may take time and will run the existing PowerShell runner.")
    if st.button("Convert / Update", disabled=not confirmed):
        try:
            result = run_convert_update_command(
                source_folder,
                conversion_output_folder,
                log_folder,
                max_files=max_files,
                full_directory=full_directory,
                timeout_minutes=timeout_minutes,
                max_attempts=max_attempts,
                cwd=Path.cwd(),
            )
        except Exception as exc:  # pragma: no cover - Streamlit UI guard.
            st.error(f"Convert / Update failed before completion: {exc}")
            return
        render_convert_update_result(result)


def render_convert_update_result(result: dict) -> None:
    st.subheader("Runner Result")
    st.metric("exit_code", result["exit_code"])
    st.write({"log_folder": result["log_folder"], **result["summary"]})
    if result["stdout"]:
        st.caption("stdout")
        st.code(result["stdout"], language="text")
    if result["stderr"]:
        st.caption("stderr")
        st.code(result["stderr"], language="text")
    if result["exit_code"] != 0:
        st.error("Runner exited with a nonzero status. Review stdout, stderr, and log files.")
    if not result["summary"]["output_exists"]:
        st.warning("Conversion output folder was not found after the runner exited.")


def render_build_library_section(conversion_output_folder: Path, library_output_folder: Path, build_command: str) -> None:
    st.subheader("Build Library")
    st.info(
        "Build Library reads the Conversion Output Folder of Knowledge Packs and writes the final searchable Library "
        "Output Folder containing library.db."
    )
    if library_output_folder.exists():
        st.warning("Library Output Folder already exists. Build Library may update files there; it will not delete source files.")
    st.code(build_command, language="powershell")
    confirmed = st.checkbox("I understand this will build or update the Library Output Folder from the Conversion Output Folder.")
    if st.button("Build Library", disabled=not confirmed):
        try:
            result = run_build_library_command(
                conversion_output_folder,
                library_output_folder,
                cwd=Path.cwd(),
            )
        except Exception as exc:  # pragma: no cover - Streamlit UI guard.
            st.error(f"Build Library failed before completion: {exc}")
        else:
            render_build_library_result(result)

    st.subheader("Load Built Library")
    summary = summarize_library_output(library_output_folder)
    st.write(summary)
    if st.button("Load Built Library"):
        if summary["is_valid_library"]:
            st.session_state["pending_library_path_value"] = str(library_output_folder)
            st.success("Loaded Library Output Folder. Library Overview, Search, and Graph View will use this path.")
            st.rerun()
        else:
            st.warning(
                "This does not look like a built library. Did you select the Conversion Output Folder instead of the "
                "Library Output Folder?"
            )


def render_build_library_result(result: dict) -> None:
    st.subheader("Build Library Result")
    st.metric("exit_code", result["exit_code"])
    st.write(result["summary"])
    if result["stdout"]:
        st.caption("stdout")
        st.code(result["stdout"], language="text")
    if result["stderr"]:
        st.caption("stderr")
        st.code(result["stderr"], language="text")
    if result["exit_code"] != 0:
        st.error("build-library exited with a nonzero status. Review stdout and stderr.")
    elif result["summary"]["is_valid_library"]:
        st.success("Library build completed and library.db was found in the Library Output Folder.")


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
