from unittest import TestCase
from unittest.mock import MagicMock, patch

from onprem_rag.services import rag_engine


class RetrievalBehaviorTests(TestCase):
    def test_vague_requests_receive_clarification(self):
        response = rag_engine.clarification_response("Help me.")

        self.assertIsNotNone(response)
        self.assertIn("summarizing", response)
        self.assertIsNone(
            rag_engine.clarification_response("Help me summarize the quality manual")
        )

    def test_summary_queries_use_broader_retrieval(self):
        with (
            patch.object(rag_engine, "TOP_K", 3),
            patch.object(rag_engine, "SUMMARY_TOP_K", 12),
        ):
            self.assertEqual(rag_engine._retrieval_limit("Where is clause 7?"), 3)
            self.assertEqual(
                rag_engine._retrieval_limit("Summarize the entire manual"),
                12,
            )

    def test_vague_request_skips_vector_collection(self):
        with patch.object(rag_engine, "_get_collection") as get_collection:
            result = rag_engine.retrieve("help me")

        self.assertFalse(result["found"])
        self.assertEqual(result["chunks"], [])
        get_collection.assert_not_called()

    def test_search_uses_summary_limit(self):
        collection = MagicMock()
        collection.count.return_value = 20
        collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        with (
            patch.object(rag_engine, "TOP_K", 3),
            patch.object(rag_engine, "SUMMARY_TOP_K", 12),
        ):
            rag_engine._search_chunks(
                collection,
                embedding=[0.1, 0.2],
                question="Give me an overview of the whole document",
            )

        self.assertEqual(collection.query.call_args.kwargs["n_results"], 12)

    def test_fallback_followed_by_an_answer_is_normalized(self):
        client = MagicMock()
        client.chat.return_value = iter(
            [
                {
                    "message": {
                        "content": (
                            "I could not find reliable supporting information in "
                            "the provided documents. However, here is an answer."
                        )
                    }
                }
            ]
        )
        chunks = [
            {
                "text": "Unrelated context.",
                "source": "manual.pdf — section 1",
                "document_name": "manual.pdf",
                "metadata": {},
            }
        ]

        with patch.object(rag_engine.ollama, "Client", return_value=client):
            stream = rag_engine.ask_stream("Explain OSP", chunks=chunks)
            streamed_text = "".join(stream)

        self.assertIn("However", streamed_text)
        self.assertEqual(
            stream.result["answer"],
            "I could not find reliable supporting information in the provided documents.",
        )
        self.assertFalse(stream.result["found"])
