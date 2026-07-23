# Launch Announcement Draft

_Edit this for your voice before posting. Three versions: LinkedIn long-form, short post, and a Hacker News / Reddit variant._

---

## Version 1 — LinkedIn (long-form)

---

**I built a local AI assistant for ISO quality manuals. Here's why.**

Quality teams spend a surprising amount of time hunting through dense ISO documents for answers they already know are in there somewhere.

"What's our CAPA close-out time for a Critical finding?"
"Which procedure covers incoming inspection?"
"What does the manual say about supplier re-evaluation?"

The answer is always in a document. It just takes 10 minutes to find.

So I built a local RAG (Retrieval-Augmented Generation) assistant that:

→ Reads your ISO 9001 / 14001 manuals and procedures
→ Answers plain-English questions with source citations
→ Runs entirely on your own hardware — no cloud, no subscription, no data leaving your building

Under the hood: PyWebView/Flask UI + ChromaDB vector store + Ollama for local LLM inference. The default model is Qwen 2.5 7B. You can benchmark against Qwen 3 8B, Gemma 3 4B, and Llama 3.1 8B from the sidebar.

It's open source and free to self-host.

📎 GitHub: [link]
📸 Demo: [link]

If you manage an ISO-certified quality system and want a custom deployment — team access, SharePoint sync, compliance dashboards — I offer consulting engagements. Details in the repo.

Happy to answer questions in the comments.

#QualityManagement #ISO9001 #AI #RAG #OpenSource #Ollama #LLM

---

## Version 2 — LinkedIn (short post)

---

Built an offline AI assistant for ISO quality documents.

Ask it anything about your manuals and procedures → get a cited answer in seconds, entirely on your own hardware.

No cloud. No subscription. No data leaving your building.

Open source: [GitHub link]

If you want a custom deployment for your team, check out the consulting page in the repo.

#ISO9001 #QualityManagement #AI #OpenSource

---

## Version 3 — Hacker News / Reddit

**Title:** Show HN: Local RAG assistant for ISO quality management documents (Ollama + ChromaDB)

---

I built a local RAG pipeline for querying ISO 9001/14001 quality manuals. After initial setup, it can run without a hosted AI API.

**What it does:**
- Ingests PDF/DOCX/TXT documents into a ChromaDB vector store
- Embeds queries with nomic-embed-text via Ollama
- Answers questions with source citations using a local LLM (Qwen 2.5 7B default)
- Desktop/browser UI with step-by-step status, model selector, and speed stats (tok/s)

**Why local?**
Quality documents often contain commercially sensitive procedures, nonconformance records, and supplier information. Sending those to a cloud API is a non-starter for most organisations.

**Technical notes:**
- Batch embeddings (32 chunks/call) for fast ingestion — 1,700 chunks takes ~5-10 min on CPU
- ChromaDB persistent client with cosine similarity
- `_StreamGen` class wraps the Ollama stream generator to carry result metadata
- Model availability checked on startup; missing models can be pulled from the UI

Tested on Windows 11 (primary), macOS, and Ubuntu 22.04.

Repo: [GitHub link]
Demo: [link]

Feedback welcome — particularly on the chunking strategy and prompt design for structured compliance documents.

---

## Post Checklist

- [ ] Add real GitHub link
- [ ] Add demo video / Loom link
- [ ] Add your name / photo / personal touch
- [ ] Remove the consulting pitch if posting to technical communities (add it as a comment if interest comes up)
- [ ] Schedule post for Tuesday–Thursday morning (highest LinkedIn engagement)
