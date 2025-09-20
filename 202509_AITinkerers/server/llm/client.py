# from abc import ABC, abstractmethod
import os
import logging
from pydantic import BaseModel
import instructor
import openai
import anthropic
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from config import settings

logger = logging.getLogger(__name__)


OPENAI_MODELS = ["gpt-4.1-2025-04-14"]
ANTHROPIC_MODELS = ["claude-sonnet-4-20250514"]


class Message(BaseModel):
    """Represents a message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Standardized response from LLM providers."""
    content: str
    model: str
    # usage: tuple[str, any] | None = None
    # finish_reason: str | None = None


class BaseLLMClient:
    """PydanticAI-based LLM client with MCP integration."""

    model: str
    openai_api_key: str
    anthropic_api_key: str
    agent: Agent
    mcp_server: MCPServerStdio

    def __init__(self, model: str = None):
        self.model = model
        self.openai_api_key = settings.openai_api_key
        self.anthropic_api_key = settings.anthropic_api_key
        self._initialize_mcp_server()
        self._initialize_agent()

    def _initialize_mcp_server(self):
        """Initialize the MCP server for Picnic integration."""
        # Get Picnic credentials from environment
        picnic_username = os.getenv("PICNIC_USERNAME")
        picnic_password = os.getenv("PICNIC_PASSWORD")

        # Check that credentials are available and not empty
        if not picnic_username or not picnic_password:
            logger.error("PICNIC_USERNAME or PICNIC_PASSWORD environment variables are missing or empty")
            raise ValueError("Picnic credentials are required but not found in environment variables")

        logger.info("Environment variables successfully checked - PICNIC credentials are present and non-empty")

        # Create environment dict with current env plus Picnic credentials
        env = os.environ.copy()
        env.update({
            "PICNIC_USERNAME": picnic_username,
            "PICNIC_PASSWORD": picnic_password
        })

        self.mcp_server = MCPServerStdio(
            "npx",
            args=["-y", "mcp-picnic"],
            timeout=30,
            env=env
        )

    def _initialize_agent(self):
        """Initialize the PydanticAI agent with model and MCP toolset."""
        if self.model in OPENAI_MODELS:
            model_name = f"openai:{self.model}"
        elif self.model in ANTHROPIC_MODELS:
            model_name = f"anthropic:{self.model}"
        else:
            raise NotImplementedError(f"Model {self.model} is not supported")

        self.agent = Agent(
            model_name,
            toolsets=[self.mcp_server],
            tool_retries=1,  # Reduce retries to avoid excessive failures
            max_tool_failures=5  # Allow some tools to fail without stopping
        )

    async def chat_completion(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = 16384,  # TODO: start using the config value
        response_model: type[BaseModel] = None,
        **kwargs
    ) -> type[BaseModel] | str:
        """Generate a chat completion with optional structured output."""

        # Convert messages to conversation string for PydanticAI
        conversation = "\n".join([
            f"{msg.role}: {msg.content}" for msg in messages
        ])

        # Use the agent with MCP tools
        async with self.agent:
            if response_model is None:
                # Return text response
                result = await self.agent.run(conversation)
                return result.output
            else:
                # Return structured response
                result = await self.agent.run(
                    conversation,
                    result_type=response_model
                )
                return result.output
