import ollama
import logging
import os
from config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        
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

# Global Ollama service instance
ollama_service = OllamaService()
