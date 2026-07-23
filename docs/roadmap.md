# Roadmap

This file tracks planned features and their status. Items are roughly ordered by priority within each version.

---

## ✅ v1.0 — Shipped

- [x] Local RAG pipeline (ChromaDB + Ollama)
- [x] PDF, DOCX, TXT document ingestion
- [x] PyWebView and Flask chat UI with source citations
- [x] Step-by-step animated status panel during queries
- [x] Live progress bar during knowledge base rebuild
- [x] Batch embeddings for fast ingestion (~32 chunks/call)
- [x] Model selector (Qwen 3 8B / Qwen 2.5 7B / Gemma 3 4B / Llama 3.1 8B)
- [x] Speed stats per response (time, token count, tok/s)
- [x] Offline-first: skip model pull if already installed
- [x] Model availability check with inline download button
- [x] Windows launcher scripts (run.bat, stop.bat)
- [x] Automated setup scripts (setup.bat, setup.sh)

---

## 🚧 v1.1 — In Progress

- [ ] **OCR support for scanned PDFs** — use Tesseract/pytesseract to extract text from image-based PDFs
- [ ] **Document metadata display** — show document revision, effective date, and status alongside citations
- [ ] **Confidence scoring** — display a retrieval confidence indicator so users know how well a question is covered
- [ ] **Multi-language support** — test and document support for non-English document sets
- [ ] **macOS/Linux launcher script** (run.sh)

---

## 📋 v1.2 — Planned

- [ ] **Document version tracking** — detect when an existing document has been updated and flag stale chunks
- [ ] **Incremental rebuild** — re-index only changed or new documents, not the entire corpus
- [ ] **Clause coverage map** — visualise which ISO clauses have good document coverage vs. gaps
- [ ] **Export conversation** — save Q&A sessions as PDF or Markdown with citations
- [ ] **Persistent chat history** — retain conversations across browser refreshes using SQLite

---

## 🔭 v2.0 — Future

- [ ] **Multi-user deployment** — shared server mode with authentication and user sessions
- [ ] **SharePoint / OneDrive sync** — automatically pull updated documents from cloud storage
- [ ] **Non-conformance detection** — scan uploaded documents and flag clauses that appear underdeveloped or missing
- [ ] **Audit trail** — log all queries, cited sources, and model used for traceability
- [ ] **Audit Trail Export** — export query history as Excel/PDF for third-party audit evidence
- [ ] **Custom system prompt editor** — let users adjust the assistant's tone, verbosity, and response format via the UI
- [ ] **REST API** — expose the RAG pipeline as an API so other internal tools can query it
- [ ] **ISO 45001 standard support** — dedicated prompt tuning for OHS management system documents
- [ ] **ISO 13485 support** — medical device quality management
- [ ] **IATF 16949 support** — automotive sector quality requirements

---

## 💡 Community Suggestions

Have an idea? Open a [feature request](../.github/ISSUE_TEMPLATE/feature_request.md) on GitHub.

---

_Last updated: June 2026_
