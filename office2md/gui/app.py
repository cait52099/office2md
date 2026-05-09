from __future__ import annotations

import streamlit as st

from office2md.gui.helpers import is_valid_library_path, load_library_overview, normalize_library_path, overview_metrics


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
        render_placeholder("Search", "Search panel is planned for v0.3.0 P2.")
    elif page == "Locate Document":
        render_placeholder("Locate Document", "Locate-document panel is planned for v0.3.0 P3.")
    elif page == "Evidence Package":
        render_placeholder("Evidence Package", "Evidence package controls are planned for v0.3.0 P4.")
    elif page == "Runner Dry-run":
        render_placeholder("Runner Dry-run", "Runner dry-run controls are planned for v0.3.0 P5.")


def render_library_overview(library_path) -> None:
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


def render_placeholder(title: str, body: str) -> None:
    st.header(title)
    st.info(body)


def _dict_rows(values: dict) -> list[dict]:
    return [{"name": key, "count": value} for key, value in values.items()]


if __name__ == "__main__":
    main()
