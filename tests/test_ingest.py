from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from onprem_rag.services.ingest import _split_text, get_source_documents, rebuild_index


class TextChunkingTests(TestCase):
    def test_split_text_preserves_content_with_overlap(self):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = _split_text(text, chunk_size=30, overlap=5)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_short_text_remains_one_chunk(self):
        self.assertEqual(_split_text("short", chunk_size=100, overlap=10), ["short"])

    def test_source_documents_only_returns_supported_files(self):
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "manual.pdf").write_bytes(b"pdf")
            (root / "notes.md").write_text("notes", encoding="utf-8")
            (root / "installer.exe").write_bytes(b"binary")

            self.assertEqual(
                [path.name for path in get_source_documents(root)],
                ["manual.pdf", "notes.md"],
            )

    def test_source_documents_handles_missing_directory(self):
        with TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / "not-created"
            self.assertEqual(get_source_documents(missing), [])

    @patch("onprem_rag.services.ingest.get_source_documents", return_value=[])
    def test_rebuild_rejects_empty_source_set(self, _mock_documents):
        with self.assertRaisesRegex(ValueError, "No supported documents"):
            rebuild_index()
