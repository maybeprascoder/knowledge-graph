import ollama
import logging
import os
from config import settings
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        self.embed_model = settings.OLLAMA_EMBED_MODEL
        
        # Configure host for global ollama client used by ollama.chat
        # Newer ollama-python expects OLLAMA_HOST or a Client(host=...).
        # We rely on the global functions, so set env var and avoid constructing a Client.
        if self.base_url:
            os.environ["OLLAMA_HOST"] = self.base_url
    
    def generate_summary(self, data: list, context: str = "expense data") -> str:
        """
        Generate a natural language summary of the provided data using Ollama
        
        Args:
            data: List of dictionaries containing the data to summarize
            context: Context description for the data type
            
        Returns:
            Natural language summary string
        """
        if not data:
            return "No data available to summarize."
        
        try:
            # Format the data for the prompt
            data_str = self._format_data_for_prompt(data)
            
            prompt = f"""
            Please provide a natural language summary of the following {context}:
            
            {data_str}
            
            Focus on:
            - Key insights and patterns
            - Total amounts and categories
            - Notable observations
            - Keep it concise but informative
            
            Summary:
            """
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes financial and business data in a clear, professional manner."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 500
                }
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Failed to generate summary with Ollama: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def _format_data_for_prompt(self, data: list) -> str:
        """Format data into a readable string for the prompt"""
        if not data:
            return "No data available"
        
        formatted_lines = []
        for i, item in enumerate(data, 1):
            line = f"{i}. "
            for key, value in item.items():
                line += f"{key}: {value}, "
            formatted_lines.append(line.rstrip(", "))
        
        return "\n".join(formatted_lines)

    def answer_question(self, question: str, context: dict) -> str:
        """Answer using ONLY provided JSON context with strict, deterministic rules.
        Generalizes across CSV-backed domains by instructing the model to:
        - search arrays (expenses, approvals, payments, vendors, facts)
        - match entities by exact/substring case-insensitive
        - extract numeric/date fields verbatim (no reformatting)
        - be concise and avoid summaries unless asked
        """
        try:
            # Ensure host is set for global client
            if settings.OLLAMA_BASE_URL:
                os.environ["OLLAMA_HOST"] = settings.OLLAMA_BASE_URL

            system = (
                "You are a careful analyst. Answer using ONLY the provided JSON context. "
                "Rules: (1) If the question asks for a specific field (e.g., date, amount, status), "
                "return the field value verbatim from the matching records. (2) Prefer exact/substring, "
                "case-insensitive matches on vendor, employee, report_id, payment_id, category. "
                "(3) If multiple matches, pick the most relevant/recent by date or highest amount when asked. "
                "(4) Do NOT invent values; if not present, say 'I don't know'. (5) Keep answers short, "
                "no bullet lists or summaries unless explicitly asked."
            )
            ctx_text = json.dumps(context, default=str)
            # Few-shot guidance for common queries (generalizable without hardcoding entities)
            prompt = (
                "Examples:\n"
                "Q: what is the expense date for vendor X?\n"
                "A: 2024-05-01\n\n"
                "Q: how much did we pay in the largest expense with vendor Y?\n"
                "A: 1371.17\n\n"
                "Q: what is the payment status for report R?\n"
                "A: PAID\n\n"
                f"Question: {question}\n\n"
                f"Context (JSON):\n{ctx_text}\n\n"
                "Return only the answer unless the user requests an explanation."
            )

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": 0.2, "num_predict": 400},
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Failed to answer question with Ollama: {e}")
            return f"Answer generation failed: {str(e)}"
    
    def _embed_one(self, text: str) -> list[float]:
        resp = ollama.embeddings(model=self.embed_model, prompt=text)
        return resp.get("embedding", [])

    def embed_parallel(self, texts: list[str], workers: int | None = None) -> list[list[float]]:
        """Parallel embedding using a thread pool to speed up CPU-bound HTTP calls."""
        try:
            if settings.OLLAMA_BASE_URL:
                os.environ["OLLAMA_HOST"] = settings.OLLAMA_BASE_URL
            if workers is None:
                workers = min(6, (os.cpu_count() or 4))
            results: list[list[float] | None] = [None] * len(texts)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(self._embed_one, t): i for i, t in enumerate(texts)}
                for fut in as_completed(futures):
                    i = futures[fut]
                    try:
                        results[i] = fut.result()
                    except Exception:
                        results[i] = []
            return [vec if vec is not None else [] for vec in results]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Compatibility wrapper; defaults to parallel embedding."""
        return self.embed_parallel(texts)

# Global Ollama service instance
ollama_service = OllamaService()
