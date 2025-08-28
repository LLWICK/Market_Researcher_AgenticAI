import asyncio
import json
from mcp import client   # ✅ correct for newer versions

async def run_pipeline(query: str):
    async with client("MCPtest") as client:
        # Step 1: Scraper
        scraper_out = await client.call("scraper", query=query)

        # Step 2: Summarizer
        summary_out = await client.call("summarizer", scraper_output=scraper_out)

        # Step 3: Research
        research_out = await client.call("research", summary_output=summary_out, query=query)

        # Step 4: Trends
        trends_out = await client.call("trends", scraper_output=scraper_out)

        results = {
            "scraper": scraper_out,
            "summarizer": summary_out,
            "research": research_out,
            "trends": trends_out,
        }

        with open("pipeline_output.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return results

if __name__ == "__main__":
    query = "What are the top competitors in Laptop market?"
    outputs = asyncio.run(run_pipeline(query))

    print("\n📊 Final Outputs:\n")
    for step, output in outputs.items():
        print(f"--- {step.upper()} ---")
        print(json.dumps(output, indent=2, ensure_ascii=False))
        print()
