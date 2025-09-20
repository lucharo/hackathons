# from abc import ABC, abstractmethod
import os
import logging
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.messages import (
    ModelMessage, ModelRequest, ModelResponse,
    SystemPromptPart, UserPromptPart, TextPart,
)
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


class ErrorResponse(BaseModel):
    """Error response when agent execution fails."""
    content: str = "I encountered an issue processing your request."
    meals: list = []
    ingredients: list = []


def to_pydantic_history(messages: list[Message]) -> list[ModelMessage]:
    """Convert Message objects to PydanticAI message history."""
    history: list[ModelMessage] = []
    for m in messages:
        if m.role == "system":
            history.append(ModelRequest(parts=[SystemPromptPart(m.content)]))
        elif m.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(m.content)]))
        elif m.role == "assistant":
            history.append(ModelResponse(parts=[TextPart(m.content)]))
    return history


class BaseLLMClient:
    """PydanticAI-based LLM client with conditional MCP integration."""

    model: str
    agent: Agent
    mcp_server: MCPServerStdio | None

    def __init__(self, model: str = None):
        self.model = model
        # Ensure API keys are set in environment for PydanticAI
        if not os.getenv("OPENAI_API_KEY") and settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if not os.getenv("ANTHROPIC_API_KEY") and settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

        # Only initialize MCP if enabled
        self.mcp_server = None
        if settings.enable_mcp:
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
            toolsets=[self.mcp_server]
        )

    async def chat_completion(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = 16384,
        response_model: type[BaseModel] = None,
        **kwargs
    ) -> BaseModel | str:
        """Generate a chat completion with optional structured output."""

        # Split messages: last user message becomes prompt, rest becomes history
        prompt = messages[-1].content
        history = to_pydantic_history(messages[:-1]) if len(messages) > 1 else None

        # Use the agent with MCP tools
        try:
            # Determine model name for agent creation
            if self.model in OPENAI_MODELS:
                model_name = f"openai:{self.model}"
            elif self.model in ANTHROPIC_MODELS:
                model_name = f"anthropic:{self.model}"
            else:
                raise NotImplementedError(f"Model {self.model} is not supported")

            # Create agent with appropriate output type and conditional toolsets
            toolsets = [self.mcp_server] if self.mcp_server is not None else []

            agent = Agent(
                model_name,
                toolsets=toolsets,
                output_type=response_model if response_model is not None else str,
                model_settings={
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                retries=3,  # Allow more overall retries
                end_strategy='exhaustive'  # Continue processing even if some tools fail
            )

            async with agent:
                result = await agent.run(prompt, message_history=history)
                return result.output
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            # Return a graceful fallback response
            fallback_message = f"I encountered some issues with the tools, but I can still help you. Error: {str(e)[:100]}..."
            if response_model is None:
                return fallback_message
            else:
                # Try to create an instance of the expected response model
                try:
                    # For most models, try to create with empty/default values
                    return response_model()
                except Exception:
                    # Return a proper BaseModel error response
                    return ErrorResponse(content=fallback_message)
