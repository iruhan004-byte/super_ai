

import sys
import os


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime

from agents import run_research_pipeline
from config import SAVE_REPORTS_TO, GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY


def check_keys():
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if missing:
        print(f"❌ Missing keys in .env: {', '.join(missing)}")
        print("   Copy .env.example to .env and paste your keys in.")
        sys.exit(1)


def save_report(result: dict) -> str:
    os.makedirs(SAVE_REPORTS_TO, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SAVE_REPORTS_TO}/report_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Research Report\n\n")
        f.write(f"**Question:** {result['query']}\n\n")
        f.write(f"**Sub-questions explored:**\n")
        for q in result["sub_questions"]:
            f.write(f"- {q}\n")
        f.write(f"\n---\n\n{result['report']}\n\n")
        f.write(f"---\n\n## Critique / Review\n\n{result['critique']}\n")

    return filename


def main():
    check_keys()

    if len(sys.argv) < 2:
        query = input("Enter your research question: ").strip()
    else:
        query = " ".join(sys.argv[1:])

    if not query:
        print("No question given. Exiting.")
        return

    result = run_research_pipeline(query)

    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(result["report"])
    print("\n" + "=" * 70)
    print("CRITIQUE")
    print("=" * 70)
    print(result["critique"])

    path = save_report(result)
    print(f"\n✅ Report saved to: {path}")


if __name__ == "__main__":
    main()
