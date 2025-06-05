# import google.generativeai as genai # Using LangChain's wrapper
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class GeminiModel:
    def __init__(self, model_name: str = "gemini-1.5-flash-latest"):
        self.model_name = model_name
        self.initial_system_prompt = os.getenv("GEMINI_PROMPT_TEMPLATE")
        # self.api_key = os.getenv("GOOGLE_API_KEY") # No longer directly using API key
        # Instead, ensure GOOGLE_APPLICATION_CREDENTIALS is set in your environment
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. Authentication might fail if not configured elsewhere.")
            # Depending on your setup, this might not be a fatal error if auth is handled by the environment

        try:
            # Initialize LangChain's ChatGoogleGenerativeAI
            # When google_api_key is not provided, it tries to authenticate using ADC (Application Default Credentials)
            # which includes checking GOOGLE_APPLICATION_CREDENTIALS.
            self.model = ChatGoogleGenerativeAI(model=self.model_name)
            logger.info(f"Gemini model '{self.model_name}' initialized successfully (attempting auth via ADC).")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model '{self.model_name}': {e}")
            raise
    def generate_response(self, user_query: str, context_chunks: List[Dict[str, str]]) -> str:
        """
        Generates a response using Gemini based on the user query and context chunks.

        Args:
            user_query (str): The user's original question.
            context_chunks (List[Dict[str, str]]): A list of dictionaries, 
                                                  each representing a code chunk 
                                                  with 'file_path' and 'content'.

        Returns:
            str: The generated response from Gemini.
        """
        system_prompt_section = self.initial_system_prompt

        context_chunks_string = ""
        for i, chunk_info in enumerate(context_chunks):
            context_chunks_string += f"--- Chunk {i+1} ---\n"
            context_chunks_string += f"File: {chunk_info.get('file_path', 'N/A')}\n"
            context_chunks_string += f"Content:\n{chunk_info.get('content', 'N/A')}\n\n"

        final_instruction = (
            "*** Important Instructions ***\n"
            "Based on the user's question and the provided code chunks,\n"
            "please select the most relevant information and generate a concise,\n"
            "easy-to-understand answer for the user.\n"
            "If none of the chunks seem relevant to the question,\n"
            "please state that you couldn't find a specific answer in the provided context.\n"
        )

        full_prompt = f"""{system_prompt_section}

A user has asked the following question about a codebase:
User Question: "{user_query}"
After performing a semantic search the following code chunks were found that might be relevant to their question.
Relevant Code Chunks:
{context_chunks_string}
{final_instruction}"""
        # logger.debug(f"Gemini Prompt: {full_prompt}")

        try:
            # LangChain's invoke method
            response = self.model.invoke(full_prompt)
            return response.content # Accessing the content from AIMessage
        except Exception as e:
            logger.error(f"Error during LangChain Gemini response generation: {e}")
            return f"Error generating response: {e}"