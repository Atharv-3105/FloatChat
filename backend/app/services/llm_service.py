import re
import json
from typing import List, Dict
from app.logging_config import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.exceptions import LLMError, SQLGenerationError
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

DB_SCHEMA = """
TABLE: argo_data
Columns:
    - float_id: TEXT (ARGO float identifier)
    - latitude: REAL (-90 to 90)
    - longitude: REAL (-180 to 180)
    - date: TEXT (ISO datetime)
    - cycle_number: REAL (ARGO float cycle_number identifier)
    - pressure: REAL (dbar, ≈ depth in meters)
    - temperature: REAL (°C)
    - salinity:  REAL (PSU)

Rules:
1. You can only write SELECT queries.
2. Always filter temperature to be between -5 and 40.
3. Always filter pressure to be between 0 and 7000.
4. Always include float_id, latitude, and longitude in the SELECT statement for mapping.
"""

SQL_PROMPT_TEMPLATE = f"""
You are an oceanographic data expert who converts user questions into SQLite SQL queries.
Given the user's question and the conversation history, generate a valid SQLite SELECT query.

---
DATABASE SCHEMA:
{DB_SCHEMA}
---
CONVERSATION HISTORY:
{{history}}
---
USER QUESTION: {{input}}
---
SQL QUERY:
"""

SUMMARY_PROMPT = """
You are an oceanographic data expert. A user asked the following question: "{user_query}"

We retrieved the following data from the database as a JSON object to answer them. This is a small sample of the full dataset.
{data_sample}

Based on this data, provide a concise, one or two-sentence summary that directly answers the user's question.
- Interpret the data in the context of the question.
- If the data shows a range of values, provide an average or a typical range.
- Do not just state what the data is (e.g., "The data contains temperature").
- Be natural and conversational.

Example:
If the user asked "What is the temperature near Mumbai?" and the data shows temperatures around 28°C, a good summary is: "The sea surface temperature near Mumbai is currently around 28°C."

Summary:
"""


class LLMService:

    def __init__(self):
        self.models = {}
        # NOTE: In a real multi-user application, memory should be managed per-user or per-session.
        self.memory = ConversationBufferMemory(memory_key="history", input_key="input")

    def _get_model(self, model_name: str, temperature: float = 0.2):
        if model_name not in self.models:
            if model_name == "gemini":
                self.models[model_name] = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=temperature,
                )
        return self.models.get(model_name)

    async def generate_sql(self, user_query: str, model_name: str = "gemini"):
        logger.debug(f"Generating SQL for query: '{user_query}'")
        try:
            prompt = PromptTemplate(
                template=SQL_PROMPT_TEMPLATE,
                input_variables=["history", "input"]
            )
            llm = self._get_model(model_name, temperature=0.0)
            if not llm:
                raise LLMError(f"Model '{model_name}' not available or configured.")

            # Using LCEL with explicit memory management
            sql_chain = prompt | llm | StrOutputParser()

            # Load history, invoke chain, then save context
            memory_variables = self.memory.load_memory_variables({})
            
            raw_response = await sql_chain.ainvoke({
                "history": memory_variables.get("history", ""),
                "input": user_query
            })
            
            self.memory.save_context({"input": user_query}, {"output": raw_response})

            logger.debug(f"Raw LLM response for SQL:\n{raw_response}\n")

            sql = self._extract_sql(raw_response)
            logger.debug(f"Extracted SQL: {sql}")

            if not self._validate_sql(sql):
                logger.warning(f"SQL validation failed for query: {sql}")
                self.memory.clear()
                raise SQLGenerationError("Generated SQL is invalid or disallowed.")

            intent = self._classify_intent(user_query)
            logger.debug(f"Classified intent: {intent}")

            return sql, intent

        except Exception as e:
            logger.error(f"LLM chain for SQL generation failed: {e}", exc_info=True)
            raise LLMError(f"LLM chain failed: {e}") from e

    async def summarize_data(self, user_query: str, data_sample: List[Dict], model_name: str = "gemini") -> str:
        if not data_sample:
            return "No data found to summarize."
        logger.debug(f"Generating summary for query: '{user_query}'")
        try:
            model = self._get_model(model_name)
            if not model:
                raise LLMError(f"Model '{model_name}' not available.")

            data_str = json.dumps(data_sample, indent=2)
            prompt = SUMMARY_PROMPT.format(user_query=user_query, data_sample=data_str)
            
            response = await model.ainvoke(prompt)
            summary = response.content.strip()
            logger.debug(f"Generated summary: {summary}")
            return summary
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}", exc_info=True)
            return f"Found {len(data_sample)} observations matching your query."

    def _extract_sql(self, response: str) -> str:
        if not response: return ""
        response = response.strip()
        code_block_pattern = r'```(?:sql|sqlite)?\s*(SELECT.*?)\s*```'
        match = re.search(code_block_pattern, response, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        select_pattern = r'(SELECT\s+.*?)(?:;|$)'
        match = re.search(select_pattern, response, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        if 'SELECT' in response.upper():
            start_idx = response.upper().find('SELECT')
            return response[start_idx:].strip().rstrip(';').rstrip('`')
        return ""

    def _validate_sql(self, sql: str) -> bool:
        if not sql: return False
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith("SELECT"): return False
        keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]
        for keyword in keywords:
            if keyword in sql_upper: return False
        return True

    def _classify_intent(self, query: str) -> str:
        query_lower = query.lower()
        if any(w in query_lower for w in ["profile", "depth", "pressure"]): return "depth_profile"
        elif any(w in query_lower for w in ["map", "location", "where"]): return "map"
        elif any(w in query_lower for w in ["compare", "between"]): return "comparison"
        else: return "table"

llm_service = LLMService()