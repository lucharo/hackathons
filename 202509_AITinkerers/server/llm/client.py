# from abc import ABC, abstractmethod
from pydantic import BaseModel
import instructor
import openai
import anthropic
from config import settings


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
    """Abstract base class for LLM clients."""

    model: str
    openai_api_key: str
    anthropic_api_key: str
    client: instructor.AsyncInstructor

    def __init__(self, model: str = None):
        self.model = model
        self.openai_api_key = settings.openai_api_key
        self.anthropic_api_key = settings.anthropic_api_key
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the instructor client based on the model provider."""
        if self.model in OPENAI_MODELS:
            # Use instructor with OpenAI
            openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            self.client = instructor.from_openai(openai_client)
        elif self.model in ANTHROPIC_MODELS:
            # Use instructor with Anthropic
            anthropic_client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
            self.client = instructor.from_anthropic(anthropic_client)
        else:
            raise NotImplementedError(f"Model {self.model} is not supported")

    async def chat_completion(
        self, 
        messages: list[Message], 
        temperature: float = 0.7,
        max_tokens: int | None = 16384,  # TODO: start using the config value
        response_model: type[BaseModel] = None,
        **kwargs
    ) -> type[BaseModel] | str:
        """Generate a chat completion with optional structured output."""
        
        # Convert messages to the format expected by instructor
        formatted_messages = [
            {"role": msg.role, "content": msg.content} 
            for msg in messages
        ]
        
        # TODO: consider allowing to equal None
        if response_model is None:
            class TextResponse(BaseModel):
                content: str
            
            response_model = TextResponse
        
        structured_response = await self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            response_model=response_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return structured_response
