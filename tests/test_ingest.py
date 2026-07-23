from unittest import TestCase

from onprem_rag.services.ingest import _split_text


class TextChunkingTests(TestCase):
    def test_split_text_preserves_content_with_overlap(self):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = _split_text(text, chunk_size=30, overlap=5)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_short_text_remains_one_chunk(self):
        self.assertEqual(_split_text("short", chunk_size=100, overlap=10), ["short"])
