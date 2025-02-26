import asyncio
import sys
from typing import List, Dict, Any, Callable

from deep_research import deep_research, write_final_report
from feedback import generate_feedback

class OutputManager:
    def log(self, *args): print(*args)
    def update_progress(self, progress): print(f"Progress: {progress}", end="\r")

output = OutputManager()
log = output.log

async def ask_question(query: str) -> str:
    print(query, end="")
    return input()

async def run():
    initial_query = await ask_question("What would you like to research? ") 
    breadth_input = await ask_question("Enter research breadth (recommended 2-10, default 4): ")
    depth_input = await ask_question("Enter research depth (recommended 1-5, default 2): ")
    
    breadth = int(breadth_input) if breadth_input.strip() else 4
    depth = int(depth_input) if depth_input.strip() else 2
    
    log("Creating research plan...")
    
    follow_up_questions = await generate_feedback({"query": initial_query})
    log("To better understand your research needs, please answer these follow-up questions:")
    
    answers = [await ask_question(f"\n{q}\nYour answer: ") for q in follow_up_questions]
    qa_pairs = " ".join(f"Q: {q} A: {a}" for q, a in zip(follow_up_questions, answers))
    combined_query = f"Initial Query: {initial_query} Follow-up Questions and Answers: {qa_pairs}"
    
    log("Researching your topic...")
    log("Starting research with progress tracking...")
    
    result = await deep_research(
        query=combined_query,
        breadth=breadth,
        depth=depth,
        on_progress=output.update_progress
    )
    
    learnings, visited_urls = result["learnings"], result["visited_urls"]
    
    log(f"Learnings: {' '.join(learnings)}")
    log(f"Visited URLs ({len(visited_urls)}): {' '.join(visited_urls)}")
    
    log("Writing final report...")
    
    report = await write_final_report({
        "prompt": combined_query,
        "learnings": learnings,
        "visited_urls": visited_urls
    })
    
    with open("output.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Final Report: {report}")
    print("Report has been saved to output.md")

if __name__ == "__main__":
    try: asyncio.run(run())
    except Exception as e: print(f"Error: {e}", file=sys.stderr)