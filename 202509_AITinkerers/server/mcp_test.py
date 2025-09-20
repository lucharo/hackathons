from llm.client import BaseLLMClient, Message
import asyncio
import logging

# Set up logging to see the environment check
logging.basicConfig(level=logging.INFO)

async def test():
  client = BaseLLMClient('claude-sonnet-4-20250514')
  messages = [Message(role='user', content='First search for pasta products on Picnic. Then try to add 2-3 different pasta products to my cart. If any fail to add, that\'s okay - just tell me which ones worked and which ones didn\'t. Also show me my current cart contents.')]
  response = await client.chat_completion(messages)
  print(response)

asyncio.run(test())
