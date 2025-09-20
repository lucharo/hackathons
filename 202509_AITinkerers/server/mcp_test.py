from llm.client import BaseLLMClient, Message
import asyncio

async def test():
  client = BaseLLMClient('claude-sonnet-4-20250514')
  messages = [Message(role='user', content='Search for pasta on Picnic')]
  response = await client.chat_completion(messages)
  print(response)

asyncio.run(test())
