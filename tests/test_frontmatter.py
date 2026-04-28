from office2md.postprocess.frontmatter import add_frontmatter


def test_add_frontmatter():
    markdown = "# Title\n"
    result = add_frontmatter(
        markdown,
        {
            "source_file": "a.txt",
            "source_path": "/tmp/a.txt",
            "checksum": "sha256:abc",
            "converter": "markitdown",
            "converted_at": "2026-04-24T00:00:00+00:00",
        },
    )

    assert result.startswith("---\n")
    assert "source_file: a.txt" in result
    assert "source_path: /tmp/a.txt" in result
    assert "checksum: sha256:abc" in result
    assert "---\n\n# Title" in result
    assert "converter: markitdown" in result
    assert "converted_at: '2026-04-24T00:00:00+00:00'" in result
