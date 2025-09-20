import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from dotenv import load_dotenv
from dedalus_labs.utils.streaming import stream_async

load_dotenv()

async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    result = await runner.run(
        input="order these pls rolled oats, unsweetened almond milk, chia seeds, vanilla protein powder, frozen mixed berries, ground cinnamon, maple syrup, firm tofu, olive oil, yellow onion, bell pepper, cherry tomatoes",
        model="openai/gpt-5-mini",
        mcp_servers=["lucharo/mcp-picnic"],
        stream=False
    )

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
