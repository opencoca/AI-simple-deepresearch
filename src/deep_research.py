import asyncio
import random

async def deep_research(query: str, breadth: int, depth: int, on_progress=None) -> dict:
    # Simulate research with delays and progress updates
    total_steps = breadth * depth
    for i in range(total_steps):
        await asyncio.sleep(0.5)  # Simulate network delay
        if on_progress:
            progress = (i + 1) / total_steps * 100
            on_progress(f"{progress:.1f}%")
    
    # Return mock data
    return {
        "learnings": [
            "Mock finding 1: Important discovery about the topic",
            "Mock finding 2: Interesting perspective found",
            f"Mock finding 3: Analysis based on depth {depth} and breadth {breadth}"
        ],
        "visited_urls": [
            "https://example.com/article1",
            "https://example.com/article2",
            "https://example.com/article3"
        ]
    }

async def write_final_report(data: dict) -> str:
    await asyncio.sleep(1)  # Simulate report generation time
    
    return f"""# Research Report

## Query
{data['prompt']}

## Key Findings
{chr(10).join('- ' + finding for finding in data['learnings'])}

## Sources
{chr(10).join('- ' + url for url in data['visited_urls'])}
"""