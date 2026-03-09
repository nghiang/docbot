import json
import logging
from google import genai
from google.genai import types
from core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            from google.oauth2 import service_account

            with open(
                settings.GOOGLE_APPLICATION_CREDENTIALS, "r", encoding="utf-8"
            ) as file:
                content = file.read()
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(content),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
            self.client = genai.Client(
                vertexai=True,
                credentials=credentials,
                project=credentials.project_id,
                location="global",
            )
        else:
            # Use API key authentication
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_content(
        self, contents, prompt: str, model_name: str = "gemini-2.5-flash"
    ):
        response = self.client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=256),
                response_mime_type="application/json",
                temperature=0.3,
                system_instruction=prompt,
            ),
            contents=contents,
        )
        if not response.text:
            raise ValueError("No content generated in the response.")
        return response

    def generate_embeddings(self, data: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            data: List of text strings to embed.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        response = self.client.models.embed_content(
            model="gemini-embedding-001",
            config=types.EmbedContentConfig(output_dimensionality=1536),
            contents=data,  # type: ignore[arg-type]
        )

        if not response.embeddings:
            raise ValueError("No embeddings found in the response.")

        return [
            list(embedding.values)
            for embedding in response.embeddings
            if embedding.values
        ]


gemini_client = GeminiClient()
