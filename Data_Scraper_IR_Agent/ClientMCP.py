import asyncio
import json
import sys
import os

# -------------------------------
# Minimal JSON-RPC Client for MCP
# -------------------------------
class SimpleMCPClient:
    def __init__(self, server_cmd):
        self.server_cmd = server_cmd
        self.process = None
        self._id = 0

    async def __aenter__(self):
        self.process = await asyncio.create_subprocess_exec(
            *self.server_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.process:
            self.process.terminate()
            await self.process.wait()

    async def call(self, tool: str, **kwargs):
        self._id += 1
        req = {
            "jsonrpc": "2.0",
            "method": tool,
            "params": kwargs,
            "id": self._id
        }
        self.process.stdin.write((json.dumps(req) + "\n").encode())
        await self.process.stdin.drain()

        resp_line = await self.process.stdout.readline()
        if not resp_line:
            err_output = await self.process.stderr.read()
            raise RuntimeError(f"No response from MCP server. STDERR:\n{err_output.decode()}")

        resp = json.loads(resp_line.decode())
        if "error" in resp:
            raise RuntimeError(f"Server error: {resp['error']}")
        return resp.get("result")


# -------------------------------
# Run the Pipeline
# -------------------------------
async def run_pipeline(query: str):
    server_script = os.path.join(os.path.dirname(__file__), "ServerMCP.py")  # replace with your server filename
    async with SimpleMCPClient([sys.executable, server_script]) as client:
        print(f"\n🔍 Running pipeline for query: {query}\n")

        # Step 1: Scraping
        scraper_out = await client.call("scraper", query=query)
        print("✅ Scraper Output:")
        print(json.dumps(scraper_out, indent=2))

        # Step 2: Summarization
        summary_out = await client.call("summarizer", scraper_output=scraper_out)
        print("\n📝 Summarizer Output:")
        print(json.dumps(summary_out, indent=2))

        # Step 3: Research
        research_out = await client.call("research", summary_output=summary_out, query=query)
        print("\n📊 Research Output:")
        print(json.dumps(research_out, indent=2))

        # Step 4: Trends
        trends_out = await client.call("trends", scraper_output=scraper_out)
        print("\n📈 Trends Output:")
        print(json.dumps(trends_out, indent=2))


if __name__ == "__main__":
    query = "AI in financial technology market"
    asyncio.run(run_pipeline(query))
