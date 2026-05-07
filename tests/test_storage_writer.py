import json

from office2md.detector import sha256_file
from office2md.storage.writer import output_dir_for_source


def test_output_dir_for_duplicate_same_name_same_checksum_uses_one_unique_target_per_checksum(tmp_path):
    source_root = tmp_path / "source"
    output_root = tmp_path / "output"
    first = source_root / "area-a" / "Part.pdf"
    second = source_root / "area-b" / "Part.pdf"
    third = source_root / "area-c" / "Part.pdf"
    for path in (first, second, third):
        path.parent.mkdir(parents=True)
        path.write_text("same content", encoding="utf-8")
    output_root.mkdir()

    first_checksum = sha256_file(first)
    first_output = output_dir_for_source(first, output_root, first_checksum)
    first_output.mkdir()
    (first_output / "manifest.json").write_text(
        json.dumps({"source_path": str(first.resolve()), "checksum": first_checksum, "status": "success"}),
        encoding="utf-8",
    )

    second_output = output_dir_for_source(second, output_root, sha256_file(second))
    third_output = output_dir_for_source(third, output_root, sha256_file(third))

    assert first_output.name == "part"
    assert second_output.name.startswith("part-")
    assert third_output == second_output
