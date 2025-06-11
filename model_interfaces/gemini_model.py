# import google.generativeai as genai # Using LangChain's wrapper
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from typing import List, Dict 
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


from model_interfaces.pydantic_parser import QueryAnalysis # Assuming UnifiedQueryAnalysis is the target parsed object
from dto.value_objects import LLMQueryResponse, UserQueryAnalysisType
from model_interfaces.prompts import gemini_prompts

logger = logging.getLogger(__name__)

class GeminiModel:
    def __init__(self, model_name: str = "gemini-1.5-flash-latest"):
        self.model_name = model_name
        self.initial_system_prompt = gemini_prompts.GEMINI_PROMPT_TEMPLATE
        self.query_analysis_prompt = gemini_prompts.QUERY_ANALYSIS_PROMPT
        self.query_analysis_parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
        self.query_response_parser = PydanticOutputParser(pydantic_object=LLMQueryResponse)



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

    def analyze_query(self, user_query: str) -> QueryAnalysis:
        """
        Analyzes the user query for relevance, grammar, and potential for direct answering.

        Args:
            user_query (str): The user's original question.

        Returns:
            QueryAnalysis: A Pydantic model instance with the analysis result.
        """
        logger.info(f"Gemini Analysis Prompt: {self.query_analysis_prompt}")
        format_instructions = self.query_analysis_parser.get_format_instructions()
        prompt = PromptTemplate(
            template=self.query_analysis_prompt,
            input_variables=["query"],
            partial_variables={"format_instructions": format_instructions}
        )
        formatted_prompt = prompt.format_prompt(query=user_query).to_string()
        logger.info(f"Gemini Analysis Prompt: {formatted_prompt}")

        try:
            response_content = self.model.invoke(formatted_prompt)
            logger.info(f"Gemini Analysis Raw Response: {response_content}")
            cleaned_response_content: str = response_content.content.strip()
            if cleaned_response_content.startswith("```json"):
                cleaned_response_content = cleaned_response_content[7:-3].strip()
            elif cleaned_response_content.startswith("```"):
                 cleaned_response_content = cleaned_response_content[3:-3].strip()
            
            return self.query_analysis_parser.parse(cleaned_response_content)
        except Exception as e:
            logger.error(f"Error during LangChain Gemini query analysis: {e}")
            return QueryAnalysis(type=UserQueryAnalysisType.ERROR, response=f"Error calling LLM or parsing for query analysis: {str(e)}")
    
    
    def generate_response(self, user_query: str, context_chunks: List[Dict[str, str]]) -> LLMQueryResponse:
        """
        Generates a response using Gemini based on the user query and context chunks.

        Args:
            user_query (str): The user's original question.
            context_chunks (List[Dict[str, str]]): A list of dictionaries, 
                                                  each representing a code chunk 
                                                  with 'file_path' and 'content'.

        Returns:
            LLMQueryResponse: The structured response from Gemini.
        """

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
            "**Constrain**" \
            "1. While referring any code chunk in the explaination, do not refer it with chunk number"
            "Refer using the file name"
        )

        format_instructions = self.query_response_parser.get_format_instructions()
        full_prompt = f"""{self.initial_system_prompt}

            User Question: "{{user_query}}"
            Relevant Code Chunks:
            {{context_chunks_string}}

            Based on the user's question and the provided code chunks:
            1. Generate a concise, easy-to-understand explanation in the 'explanation' field.
            2. If none of the chunks seem relevant to the question, state that you couldn't find a specific answer in the provided context within the 'explanation' field.
            3. If code chunks were used to formulate the explanation, include them in the 'code_references' list. Each item in the list should be an object with 'file_name' and 'code_content'. If no specific chunks are directly referenced in the explanation, this list can be empty.
            4. Respond STRICTLY in JSON format. Follow the JSON schema provided below.

            {{format_instructions}}
            JSON Response:
            """
        logger.info(f"Gemini Prompt: {full_prompt}")
        prompt = PromptTemplate(
            template=full_prompt,
            input_variables=["user_query", "context_chunks_string"],
            partial_variables={"format_instructions": format_instructions}
        )
        full_prompt = prompt.format_prompt(
            user_query=user_query, 
            context_chunks_string=context_chunks_string
        ).to_string()
        logger.info(f"Gemini Generate Response Prompt: {full_prompt}")
        try:
            # LangChain's invoke method
            response_content = self.model.invoke(full_prompt)
            logger.info(f"Gemini Generate Response Raw Output: {response_content}")
            cleaned_response_content = response_content.content.strip()
            if cleaned_response_content.startswith("```json"):
                cleaned_response_content = cleaned_response_content[7:-3].strip()
            elif cleaned_response_content.startswith("```"):
                 cleaned_response_content = cleaned_response_content[3:-3].strip()
            return self.query_response_parser.parse(cleaned_response_content)
        except Exception as e:
            logger.error(f"Error during LangChain Gemini response generation: {e}")
            return LLMQueryResponse(explanation=f"Error generating response: {e}", code_references=[])
        


    def generate_code_diff(self, user_query: str, context_chunks: List[Dict[str, str]]) -> str:
        """
        Generates a code change in unified diff format based on user query and context.

        Args:
            user_query (str): The user's original question/request for code change.
            context_chunks (List[Dict[str, str]]): A list of dictionaries,
                                                  each representing a code chunk
                                                  with 'file_path' and 'content'.

        Returns:
            str: The generated unified diff content as a string.
        """
    
        if not self.model:
            raise RuntimeError("Gemini model not initialized.")
        DIFF_GENERATION_PROMPT= """You are an expert at providing code changes for a laravel project.You are given with the codebase outline. Your task is to generate a code change in the unified diff format based on the user's request and the provided code context.
            Analyze the user's request and the relevant code chunks. Determine what code needs to be added, removed, or modified.
            Generate the output STRICTLY in the unified diff format.
            Rules for the diff format:
            - Start with `--- a/full/path/to/original/file`
            - Follow with `+++ b/full/path/to/modified/file` (usually the same path)
            - Use `@@ ... @@` lines to indicate hunk headers (line numbers and counts).
            - Lines starting with `-` are removed lines.
            - Lines starting with `+` are added lines.
            - Lines starting with ` ` (a single space) are context lines (unchanged lines shown for context). <--- ADD THIS CLARIFICATION
            - Ensure the diff is syntactically correct and can be applied using a standard patch tool.
            - If the request is unclear or cannot be fulfilled based on the context, provide an empty diff or explain why in a comment within the diff format (e.g., starting lines with `#`).

            ***Constraint***
            1. From the given code chunks, find the best match chunk for the user query and do the code changes.
            2. It is possible that code changes may be required in two or more different chuks in different fils.
            3. Provide all the relevant code changes at once.

            User Request: "{user_query}"

            Relevant Code Chunks:
            {context_chunks_string}

            Generate the unified diff below:
            """
        


        context_chunks_string = ""
        for i, chunk_info in enumerate(context_chunks):
            context_chunks_string += f"--- Chunk {i+1} ---\n"
            context_chunks_string += f"File: {chunk_info.get('file_path', 'N/A')}\n"
            context_chunks_string += f"Content:\n{chunk_info.get('content', 'N/A')}\n\n"
        prompt = PromptTemplate(
            template=DIFF_GENERATION_PROMPT, # Use the new diff prompt
            input_variables=["user_query", "context_chunks_string"],
        )
        full_prompt = prompt.format_prompt(
            user_query=user_query,
            context_chunks_string=context_chunks_string
        ).to_string()

        logger.info(f"Gemini Diff Generation Prompt: {full_prompt}")

        response = self.model.invoke(full_prompt)
        logger.info(f"Gemini Diff Generation Raw Output: {response.content}")
        cleaned_response_content = response.content.strip()
        if cleaned_response_content.startswith("```json"):
            cleaned_response_content = cleaned_response_content[7:-3].strip()
        elif cleaned_response_content.startswith("```"):
                cleaned_response_content = cleaned_response_content[3:-3].strip()
        return cleaned_response_content 