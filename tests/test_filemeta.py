import pytest

from mailforen.modules.forensic.filemeta import file_meta


class TestExtract:
    def test_text_file_metadata(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("hello world")

        results = file_meta.extract(path)

        assert "error" not in results
        assert results["filename"] == "notes.txt"
        assert results["size_bytes"] == 11
        assert results["extension"] == ".txt"
        assert results["size_human"] == "11.0 B"
        # ISO timestamps parse cleanly
        from datetime import datetime

        datetime.fromisoformat(results["created"])
        datetime.fromisoformat(results["modified"])
        datetime.fromisoformat(results["accessed"])

    def test_missing_file(self, tmp_path):
        results = file_meta.extract(tmp_path / "ghost.bin")

        assert results == {"error": "File not found"}

    def test_extension_normalised_lower_case(self, tmp_path):
        path = tmp_path / "Photo.JPG"
        path.write_bytes(b"\xff\xd8\xff")  # not a valid JPEG; EXIF just won't be found

        results = file_meta.extract(path)

        assert results["extension"] == ".jpg"
        assert "exif" not in results

    def test_jpeg_without_exif_has_no_exif_key(self, tmp_path):
        path = tmp_path / "plain.jpg"
        path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)

        results = file_meta.extract(path)

        assert "error" not in results
        assert "exif" not in results


class TestHumanSize:
    @pytest.mark.parametrize("size,expected", [
        (0, "0.0 B"),
        (1, "1.0 B"),
        (512, "512.0 B"),
        (1023.9, "1023.9 B"),
        (1024, "1.0 KB"),
        (2048, "2.0 KB"),
        (1024 ** 2, "1.0 MB"),
        (1024 ** 3, "1.0 GB"),
        (1024 ** 4, "1.0 TB"),
        (1024 ** 4 * 2.5, "2.5 TB"),
    ])
    def test_units(self, size, expected):
        assert file_meta.human_size(size) == expected
