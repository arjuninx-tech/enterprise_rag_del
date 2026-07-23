"""
prompts.py
──────────
Module 9.4 — Prompt Module
Stores the strict system prompt, answer formatting instructions,
and the mandatory fallback response as defined in FR-10.
"""

# ── System Prompt (FR-10) ─────────────────────────────────────────────────────
# This prompt is injected into every LLM request.
# Do NOT modify these rules without updating the requirements document.

SYSTEM_PROMPT = """You are an ISO 9001 and ISO 14001 manual assistant for internal company use.

Rules:
1. Answer ONLY from the provided context. Do not use any external knowledge.
2. Do NOT invent ISO procedures, clauses, responsibilities, records, or compliance claims.
3. If the answer is not found in the context, respond with EXACTLY:
   "This information is not available in the approved documents provided."
4. Always mention the source document name and section/page whenever available.
5. Keep answers clear, professional, and audit-friendly.
6. Do NOT provide legal, certification, or compliance guarantees.
7. If the question is unclear, ask for clarification before answering.
"""

# ── Mandatory fallback response (FR-05) ───────────────────────────────────────
NOT_FOUND_RESPONSE = (
    "This information is not available in the approved documents provided."
)

# ── RAG prompt template ───────────────────────────────────────────────────────
# Used to construct the final prompt sent to the LLM.

SYSTEM_PROMPT_WITH_ATTACHMENTS = """You are an intelligent document assistant.

You have access to:
1. Documents the user has attached directly to this conversation
2. The company's approved ISO document knowledge base (when relevant)

Your capabilities:
- Answer questions based on the provided documents
- Summarise: produce clear, structured summaries of attached documents
- Compare: compare two or more documents side by side (differences, similarities)
- Extract: pull specific data, tables, clauses, or sections from documents
- Analyse: identify gaps, risks, or compliance issues

Rules:
1. Base answers on the provided context. Cite document names when referencing them.
2. For comparison tasks, use a structured side-by-side format.
3. For summaries, organise by key topics or sections.
4. If information is not in any provided context, say so clearly.
5. Keep answers professional and concise.
"""


def build_prompt_with_attachments(
    question: str,
    attached_context: str,
    context_chunks: list[dict] | None = None,
) -> str:
    """
    Build prompt when the user has attached documents to the chat.
    Combines in-memory attached docs with optional KB chunks.
    """
    parts: list[str] = []

    if attached_context:
        parts.append("=== USER-ATTACHED DOCUMENTS ===\n\n" + attached_context)

    if context_chunks:
        kb_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            src = chunk.get("source", "Knowledge Base")
            kb_parts.append(f"[KB Context {i} — {src}]\n{chunk['text']}")
        parts.append("=== KNOWLEDGE BASE CONTEXT ===\n\n" + "\n\n---\n\n".join(kb_parts))

    context_block = "\n\n" + "\n\n".join(parts) + "\n\n" if parts else ""

    return (
        f"{SYSTEM_PROMPT_WITH_ATTACHMENTS}"
        f"{context_block}"
        f"User request: {question}\n\n"
        f"Answer (cite document names where relevant):"
    )


def build_rag_prompt(question: str, context_chunks: list[dict]) -> str:
    """
    Build the full prompt combining system instructions, retrieved context,
    and the user question.

    Args:
        question:       The user's question.
        context_chunks: List of dicts with keys 'text' and 'source'.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        source_label = chunk.get("source", "Unknown Document")
        context_parts.append(f"[Context {i} — Source: {source_label}]\n{chunk['text']}")

    context_block = "\n\n---\n\n".join(context_parts)

    prompt = f"""{SYSTEM_PROMPT}

=== APPROVED DOCUMENT CONTEXT ===

{context_block}

=== END OF CONTEXT ===

Based ONLY on the context above, answer the following question:

Question: {question}

Answer (include source document name and section/page where available):"""

    return prompt
