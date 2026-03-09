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
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY, vertexai=True)

    def generate_answer(self, question: str, context: str, model_name: str = "gemini-2.5-flash") -> str:
        """Generate an answer to a question given relevant context.

        Args:
            question: The user's question.
            context: Retrieved document context.
            model_name: Gemini model to use.

        Returns:
            Generated answer text.
        """
        system_prompt = (
            "You are a helpful document QA assistant. "
            "Answer the user's question based ONLY on the provided context. "
            "If the context doesn't contain enough information to answer, say so clearly. "
            "Cite the source document and page number when possible."
        )

        user_prompt = f"""Context from documents:
{context}

Question: {question}

Please answer the question based on the context above."""

        response = self.client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=system_prompt,
            ),
            contents=user_prompt,
        )
        if not response.text:
            raise ValueError("No content generated in the response.")
        return response.text


gemini_client = GeminiClient()
