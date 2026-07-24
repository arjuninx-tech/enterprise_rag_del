from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch

from onprem_rag.services import ingest as ingest_module
from onprem_rag.services.ingest import _split_text, get_source_documents, rebuild_index


class TextChunkingTests(TestCase):
    def test_split_text_preserves_content_with_overlap(self):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = _split_text(text, chunk_size=30, overlap=5)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_short_text_remains_one_chunk(self):
        self.assertEqual(_split_text("short", chunk_size=100, overlap=10), ["short"])

    def test_short_sentences_do_not_create_micro_chunks(self):
        text = " ".join(f"Requirement {number} must be verified." for number in range(200))
        chunks = _split_text(text, chunk_size=600, overlap=80)

        self.assertLess(len(chunks), 20)
        self.assertGreater(min(len(chunk) for chunk in chunks[:-1]), 300)

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

    def test_delete_and_clear_managed_source_documents(self):
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            documents = root / "documents"
            documents.mkdir()
            first = documents / "first.txt"
            second = documents / "second.md"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")

            with (
                patch.object(ingest_module, "DOCS_PATH", documents),
                patch.object(ingest_module, "CHROMA_PATH", root / "vector-db"),
            ):
                deleted = ingest_module.delete_knowledge_document("first.txt")
                self.assertTrue(deleted["removed_source"])
                self.assertFalse(first.exists())

                cleared = ingest_module.clear_knowledge_base()
                self.assertEqual(cleared["removed_files"], ["second.md"])
                self.assertFalse(second.exists())

    def test_delete_succeeds_when_vector_collection_was_already_cleared(self):
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            documents = root / "documents"
            vector_db = root / "vector-db"
            documents.mkdir()
            vector_db.mkdir()
            source = documents / "manual.pdf"
            source.write_bytes(b"pdf")
            client = MagicMock()
            client.list_collections.return_value = []

            with (
                patch.object(ingest_module, "DOCS_PATH", documents),
                patch.object(ingest_module, "CHROMA_PATH", vector_db),
                patch.object(
                    ingest_module.chromadb,
                    "PersistentClient",
                    return_value=client,
                ),
            ):
                deleted = ingest_module.delete_knowledge_document("manual.pdf")

            self.assertTrue(deleted["removed_source"])
            self.assertEqual(deleted["removed_chunks"], 0)
            self.assertFalse(source.exists())
            client.get_collection.assert_not_called()
