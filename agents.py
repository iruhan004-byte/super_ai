"""
Multi-agent research pipeline — each agent runs on the model best suited to it:

  Planner      -> breaks the question into sub-questions        (Groq/Llama, fast)
  Researcher   -> searches + gathers evidence per sub-question   (DuckDuckGo)
  Synthesizer  -> writes the final report from all evidence      (Gemini, long context)
  Critic       -> checks the report for gaps/contradictions      (OpenRouter free-router)

Each function is independent, so you can swap providers per-agent later
without touching the others.
"""

import json
from provider import ask_gemini, ask_groq, ask_critic
from search_tool import search_and_gather
from config import MAX_SUB_QUESTIONS


# ---------------------------------------------------------------------------
# 1. PLANNER
# ---------------------------------------------------------------------------
def plan_sub_questions(user_query: str) -> list[str]:
    prompt = f"""You are a research planner. Break the user's question into
{MAX_SUB_QUESTIONS} or fewer specific, non-overlapping search queries that
together would let someone answer it thoroughly.

User question: "{user_query}"

Return ONLY a JSON array of strings, nothing else. Example:
["query one", "query two", "query three"]
"""
    raw = ask_groq(prompt, system="You output only valid JSON arrays of strings.")
    try:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        sub_questions = json.loads(cleaned)
        if isinstance(sub_questions, list) and all(isinstance(q, str) for q in sub_questions):
            return sub_questions[:MAX_SUB_QUESTIONS]
    except Exception as e:
        print(f"[Planner] JSON parse failed: {e}\nRaw output: {raw}")

    # fallback: just use the original query if planning fails
    return [user_query]


# ---------------------------------------------------------------------------
# 2. RESEARCHER
# ---------------------------------------------------------------------------
def research_sub_question(sub_question: str) -> dict:
    """
    Returns {question, sources: [{title, url, snippet, content}]}
    """
    print(f"  🔎 Researching: {sub_question}")
    gathered = search_and_gather(sub_question)
    return {"question": sub_question, "sources": gathered}


def run_research(sub_questions: list[str]) -> list[dict]:
    return [research_sub_question(q) for q in sub_questions]


# ---------------------------------------------------------------------------
# 3. SYNTHESIZER
# ---------------------------------------------------------------------------
def synthesize_report(user_query: str, research_data: list[dict]) -> str:
    evidence_blocks = []
    for item in research_data:
        block = f"### Sub-question: {item['question']}\n"
        for src in item["sources"]:
            text = src["content"] or src["snippet"]
            block += f"- **{src['title']}** ({src['url']})\n  {text[:1200]}\n"
        evidence_blocks.append(block)

    evidence_text = "\n\n".join(evidence_blocks)

    prompt = f"""You are a research synthesizer. Using ONLY the evidence below,
write a clear, well-organized report answering the user's question.

Rules:
- Cite sources inline like [Source: <title>] after claims.
- If evidence conflicts, mention the conflict explicitly.
- If evidence is insufficient for some part of the question, say so honestly.
- Use headings and short paragraphs. Do not invent facts not in the evidence.

User question: "{user_query}"

EVIDENCE:
{evidence_text}

Write the report now.
"""
    return ask_gemini(prompt, system="You are a precise, honest research report writer.")


# ---------------------------------------------------------------------------
# 4. CRITIC  (OpenRouter free router — auto-picks a currently free model)
# ---------------------------------------------------------------------------
def critique_report(user_query: str, report: str) -> str:
    prompt = f"""You are a critical reviewer. Check this research report for:
1. Unsupported or vague claims
2. Missing angles on the original question
3. Internal contradictions

Original question: "{user_query}"

REPORT:
{report}

Give a short bullet list of issues found (or say "No major issues found"
if the report is solid). Be concise.
"""
    return ask_critic(prompt, system="You are a rigorous, concise fact-checker.")


# ---------------------------------------------------------------------------
# FULL PIPELINE
# ---------------------------------------------------------------------------
def run_research_pipeline(user_query: str) -> dict:
    print(f"\n🧠 Planning research for: {user_query}")
    sub_questions = plan_sub_questions(user_query)
    print(f"   Sub-questions: {sub_questions}")

    research_data = run_research(sub_questions)

    print("✍️  Synthesizing report...")
    report = synthesize_report(user_query, research_data)

    print("🔍 Running critique pass...")
    critique = critique_report(user_query, report)

    return {
        "query": user_query,
        "sub_questions": sub_questions,
        "report": report,
        "critique": critique,
    }