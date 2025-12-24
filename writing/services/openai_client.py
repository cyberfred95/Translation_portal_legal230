import logging
from typing import Optional
from dataclasses import dataclass
from openai import OpenAI, RateLimitError, AuthenticationError, APIError
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class OpenAIResponse:
    """Response wrapper for OpenAI API calls."""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None


class OpenAIClientError(Exception):
    """Exception raised for OpenAI client configuration errors."""
    pass


class OpenAIClient:
    """
    HTTP client for OpenAI Chat Completion API.

    Handles:
    - API key configuration
    - Chat completion requests
    - Error handling and logging
    """

    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not self.api_key:
            raise OpenAIClientError("OPENAI_API_KEY not configured in settings")

        self.client = OpenAI(api_key=self.api_key)

    def process_text(
        self,
        text: str,
        prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        variables: dict = None
    ) -> OpenAIResponse:
        """
        Process text with GPT using chat completion.

        Args:
            text: Input text to process
            prompt: System prompt template
            model: GPT model to use (e.g., "gpt-4", "gpt-4o", "gpt-3.5-turbo")
            temperature: Sampling temperature (0-1)
            variables: Variables to substitute in prompt template

        Returns:
            OpenAIResponse with result or error
        """
        try:
            formatted_prompt = self._format_prompt(prompt, variables or {})

            logger.info(f"OpenAI request: model={model}, temperature={temperature}")

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": formatted_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=temperature
            )

            content = response.choices[0].message.content

            logger.info(
                f"OpenAI success: {response.usage.total_tokens} tokens "
                f"(prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens})"
            )

            return OpenAIResponse(
                success=True,
                content=content
            )

        except RateLimitError:
            error_msg = "OpenAI rate limit exceeded. Please try again in a moment."
            logger.warning(error_msg)
            return OpenAIResponse(success=False, error=error_msg)

        except AuthenticationError:
            error_msg = "OpenAI API authentication failed. Please check configuration."
            logger.error(error_msg)
            return OpenAIResponse(success=False, error=error_msg)

        except APIError as e:
            error_msg = f"OpenAI service error: {str(e)}"
            logger.error(error_msg)
            return OpenAIResponse(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error during OpenAI processing: {str(e)}"
            logger.error(error_msg)
            return OpenAIResponse(success=False, error=error_msg)

    def _format_prompt(self, prompt: str, variables: dict) -> str:
        """
        Format prompt template with variables.

        Replaces {variable_name} placeholders with values from variables dict.
        """
        formatted = prompt
        for key, value in variables.items():
            formatted = formatted.replace(f"{{{key}}}", str(value))
        return formatted
