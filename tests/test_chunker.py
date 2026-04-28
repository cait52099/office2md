from office2md.postprocess.chunker import chunk_markdown


def test_chunk_markdown_keeps_heading_path():
    markdown = "# Title\n\nIntro\n\n## Section\n\nBody"

    chunks = chunk_markdown(markdown, "sample.txt", "sample")

    assert chunks[0]["heading_path"] == ["Title"]
    assert chunks[1]["heading_path"] == ["Title", "Section"]
    assert chunks[0]["chunk_id"] == "sample_0001"


def test_chunk_markdown_splits_long_text():
    markdown = "# Title\n\n" + ("word " * 500)

    chunks = chunk_markdown(markdown, "sample.txt", "sample", max_chars=100)

    assert len(chunks) > 1
    assert all(chunk["char_count"] <= 100 for chunk in chunks)

