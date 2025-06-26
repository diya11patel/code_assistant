import os
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.logger import LOGGER
from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import json
import re

from model_interfaces.pydantic_parser import QueryAnalysis
from dto.value_objects import LLMQueryResponse, UserQueryAnalysisType
from model_interfaces.prompts import gemini_prompts
from transformers import GPT2TokenizerFast

class GeminiModel:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.model_name = model_name
        self.initial_system_prompt = gemini_prompts.GEMINI_PROMPT_TEMPLATE
        self.query_analysis_prompt = gemini_prompts.QUERY_ANALYSIS_PROMPT
        self.query_analysis_parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
        self.query_response_parser = PydanticOutputParser(pydantic_object=LLMQueryResponse)
        self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")  # Initialize tokenizer
        self.max_tokens = 4096  # Assumed token limit for Gemini

        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            LOGGER.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. Authentication might fail if not configured elsewhere.")

        try:
            self.model = ChatGoogleGenerativeAI(model=self.model_name)
            LOGGER.info(f"Gemini model '{self.model_name}' initialized successfully (attempting auth via ADC).")
        except Exception as e:
            LOGGER.error(f"Failed to initialize Gemini model '{self.model_name}': {e}")
            raise

    def analyze_query(self, user_query: str) -> QueryAnalysis:
        format_instructions = self.query_analysis_parser.get_format_instructions()
        prompt = PromptTemplate(
            template=self.query_analysis_prompt,
            input_variables=["query"],
            partial_variables={"format_instructions": format_instructions}
        )
        formatted_prompt = prompt.format_prompt(query=user_query).to_string()
        LOGGER.info(f"Gemini Analysis Prompt: {formatted_prompt}")

        try:
            response_content = self.model.invoke(formatted_prompt)
            cleaned_response_content = response_content.content.strip()
            if cleaned_response_content.startswith("```json"):
                cleaned_response_content = cleaned_response_content[7:-3].strip()
            elif cleaned_response_content.startswith("```"):
                cleaned_response_content = cleaned_response_content[3:-3].strip()
            return self.query_analysis_parser.parse(cleaned_response_content)
        except Exception as e:
            LOGGER.error(f"Error during LangChain Gemini query analysis: {e}")
            return QueryAnalysis(type=UserQueryAnalysisType.ERROR, response=f"Error calling LLM or parsing for query analysis: {str(e)}")

    def generate_response(self, user_query: str, context_chunks: List[Dict[str, str]]) -> LLMQueryResponse:
        context_chunks_string = "\n".join(
            f"--- Chunk {i+1} ---\nFile: {chunk.get('file_path', 'N/A')}\nContent:\n{chunk.get('content', 'N/A')}"
            for i, chunk in enumerate(context_chunks)
        )
        format_instructions = self.query_response_parser.get_format_instructions()
        full_prompt = f"""{self.initial_system_prompt}

            User Question: "{{user_query}}"
            Relevant Code Chunks:
            {{context_chunks_string}}

            Based on the user's question and the provided code chunks:
            1. Generate a concise, easy-to-understand explanation in the 'explanation' field.
            2. If none of the chunks seem relevant, state that you couldn't find a specific answer in the provided context.
            3. If code chunks were used, include them in 'code_references' with 'file_name' and 'code_content'.
            4. Respond STRICTLY in JSON format.

            {{format_instructions}}
            JSON Response:
            """
        prompt = PromptTemplate(
            template=full_prompt,
            input_variables=["user_query", "context_chunks_string"],
            partial_variables={"format_instructions": format_instructions}
        )
        full_prompt = prompt.format_prompt(user_query=user_query, context_chunks_string=context_chunks_string).to_string()
        try:
            response_content = self.model.invoke(full_prompt)
            cleaned_response_content = response_content.content.strip()
            if cleaned_response_content.startswith("```json"):
                cleaned_response_content = cleaned_response_content[7:-3].strip()
            elif cleaned_response_content.startswith("```"):
                cleaned_response_content = cleaned_response_content[3:-3].strip()
            return self.query_response_parser.parse(cleaned_response_content)
        except Exception as e:
            LOGGER.error(f"Error during LangChain Gemini response generation: {e}")
            return LLMQueryResponse(explanation=f"Error generating response: {e}", code_references=[])

    def generate_modified_code(self, user_query: str, context_chunks: List[Dict[str, str]]) -> str:
        if not self.model:
            raise RuntimeError("Gemini model not initialized.")
        
        context_chunks_string = "\n".join(
            f"--- Chunk {i+1} ---\nFile: {chunk.get('file_path', 'N/A')}\nContent:\n{chunk.get('content', 'N/A')}"
            for i, chunk in enumerate(context_chunks)
        )
        prompt = PromptTemplate(
            template=gemini_prompts.FULL_CODE_MODIFICATION_PROMPT,
            input_variables=["user_query", "context_chunks_string"],
        )
        full_prompt = prompt.format_prompt(user_query=user_query, context_chunks_string=context_chunks_string).to_string()

        response = self.model.invoke(full_prompt)
        cleaned_response_content = response.content.strip()
        if cleaned_response_content.startswith("```php"):
            cleaned_response_content = cleaned_response_content[6:-3].strip()
        elif cleaned_response_content.startswith("```"):
            cleaned_response_content = cleaned_response_content[3:-3].strip()
        return cleaned_response_content     

    def generate_code_diff(self, user_query: str, context_chunks: List[Dict[str, str]],file_path: str) -> str:
        if not self.model:
            raise RuntimeError("Gemini model not initialized.")

        context_chunks_string = "\n".join(
            f"--- Chunk {i+1} ---\nFile: {chunk.get('file_path', 'N/A')}\nType: {chunk.get('type', 'N/A')}\nName: {chunk.get('name', 'N/A')}\nStart Line: {chunk.get('start_line', 'N/A')}\nEnd Line: {chunk.get('end_line', 'N/A')}\nContent:\n{chunk.get('content', 'N/A')}"
            for i, chunk in enumerate(context_chunks)
        )
        prompt = PromptTemplate(
            template=gemini_prompts.DIFF_GENERATION_PROMPT,
            input_variables=["user_query", "context_chunks_string","file_path"],
        )
        full_prompt = prompt.format_prompt(user_query=user_query, context_chunks_string=context_chunks_string, file_path=file_path).to_string()
        response = self.model.invoke(full_prompt)
        cleaned_response_content = response.content.strip()
        if cleaned_response_content.startswith("```json"):
            cleaned_response_content = cleaned_response_content[7:-3].strip()
        elif cleaned_response_content.startswith("```"):
            cleaned_response_content = cleaned_response_content[3:-3].strip()
        return cleaned_response_content 

    def generate_batch_modified_code(self, user_query: str, context_chunks: List[Dict[str, str]]) -> Dict[int, str]:
        if not self.model:
            raise RuntimeError("Gemini model not initialized.")

        context_chunks_string = "\n".join(
            f"--- Chunk {i} ---\nFile: {chunk.get('file_path', 'N/A')}\nContent:\n{chunk.get('content', 'N/A')}\nStart Line: {chunk.get('start_line', 'N/A')}\nEnd Line: {chunk.get('end_line', 'N/A')}"
            for i, chunk in enumerate(context_chunks)
        )

        prompt = PromptTemplate(
            template=gemini_prompts.BATCH_CODE_GENERATION_PROMPT,
            input_variables=["user_query", "context_chunks_string"]
        )

        try:
            full_prompt = prompt.format_prompt(user_query=user_query, context_chunks_string=context_chunks_string).to_string()
            response = self.model.invoke(full_prompt)
            cleaned_response_content = response.content.strip()
            LOGGER.info(f"Gemini Batch Modification Raw Response: {cleaned_response_content}")
            if cleaned_response_content.startswith("```json"):
                cleaned_response_content = cleaned_response_content[7:-3].strip()
            elif cleaned_response_content.startswith("```"):
                cleaned_response_content = cleaned_response_content[3:-3].strip()

            if not cleaned_response_content.startswith("{") and not cleaned_response_content.endswith("}"):
                leaned_response_content = "{" + cleaned_response_content + "}"
                LOGGER.warning(f"Attempted to fix malformed JSON by adding braces: {cleaned_response_content}")

            return json.loads(cleaned_response_content)
        except json.JSONDecodeError as e:
            LOGGER.error(f"JSON decoding error in generate_batch_modified_code: {e}. Raw response: {cleaned_response_content}")
            return {}
        except Exception as e:
            LOGGER.error(f"Error generating batch modified code: {e}. Raw response: {cleaned_response_content if 'cleaned_response_content' in locals() else 'N/A'}")
            return {}
