import google.generativeai as genai
from typing import Dict, List, Optional
import logging
import json
from app.core.config import settings
from app.services.schema_selector import SchemaSelector

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GOOGLE_MODEL)
        self.schema_selector = SchemaSelector()

    def generate_sql(self, question: str) -> Dict[str, str]:
        """
        Generate SQL from natural language question using Google Generative AI.
        
        Args:
            question: Natural language question
        
        Returns:
            Dictionary with 'sql' and 'explanation' keys
        """
        try:
            # Get relevant schema
            relevant_schema = self.schema_selector.get_relevant_schema(question)
            schema_text = self.schema_selector.format_schema_for_prompt(relevant_schema)
            
            logger.info(f"Schema being sent to AI:\n{schema_text}")
            
            # Build system prompt
            system_prompt = self._build_system_prompt(schema_text)
            
            # Call Gemini API
            prompt = f"{system_prompt}\n\nQuestion: {question}\n\nGenerate the SQL required to answer this question. Return ONLY the SQL query, nothing else. Do not include any explanations or JSON formatting."
            
            logger.info(f"Sending prompt to Gemini: {prompt[:500]}...")
            response = self.model.generate_content(prompt)
            
            logger.info(f"Raw Gemini response: {response}")
            logger.info(f"Response type: {type(response)}")
            
            if hasattr(response, 'text'):
                content = response.text.strip()
                logger.info(f"Response text: {content}")
            else:
                logger.error("Response has no text attribute")
                content = ""
            
            # Clean up the response - remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("sql"):
                    content = content[3:]
                content = content.strip()
            
            sql = content.strip()
            
            logger.info(f"Generated SQL for question: {question}")
            logger.info(f"SQL: {sql}")
            
            return {
                "sql": sql,
                "explanation": ""
            }
            
        except Exception as e:
            logger.error(f"Google AI API error: {e}")
            raise

    def format_result(self, question: str, sql: str, data: List[Dict]) -> str:
        """Format database query result into natural language answer."""
        try:
            logger.info(f"format_result called with question: {question}, data: {data}")
            
            if not data:
                logger.warning("No data to format")
                return "No matching records found."
            
            # Build system prompt for formatting
            system_prompt = """You are a helpful assistant that formats database query results into natural language answers.
Your job is to convert the database result into a clear, human-readable answer to the user's question.
Be concise and accurate. Do not invent information not present in the data."""
            
            # Format data for prompt
            data_str = str(data)
            
            prompt = f"{system_prompt}\n\nQuestion: {question}\n\nDatabase result: {data_str}\n\nProvide a clear, natural language answer."
            
            logger.info(f"Formatting result with data: {data_str}")
            response = self.model.generate_content(prompt)
            
            if response and hasattr(response, 'text'):
                answer = response.text.strip()
                logger.info(f"AI formatted answer: {answer}")
                
                if not answer:
                    logger.warning("AI returned empty answer, using fallback")
                    # Fallback to simple formatting
                    if len(data) == 1:
                        return f"Found 1 record: {data[0]}"
                    return f"Found {len(data)} records: {data}"
                
                return answer
            else:
                logger.error("AI response is invalid or has no text attribute")
                # Fallback to simple formatting
                if len(data) == 1:
                    return f"Found 1 record: {data[0]}"
                return f"Found {len(data)} records: {data}"
            
        except Exception as e:
            logger.error(f"Result formatting error: {e}", exc_info=True)
            # Fallback to simple formatting
            if len(data) == 1:
                return f"Found 1 record: {data[0]}"
            return f"Found {len(data)} records: {data}"

    def _build_system_prompt(self, schema_text: str) -> str:
        """Build system prompt for SQL generation."""
        return f"""You are a SQL generation assistant for a Smart Inventory Management System.

Your job is to convert the administrator's natural-language question into a read-only SQL query.

CRITICAL RULES:
1. Generate READ-ONLY SQL only.
2. Only SELECT statements are allowed.
3. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, or REVOKE.
4. NEVER modify database data or database structure.
5. You MUST use ONLY the tables and columns provided in the schema below.
6. NEVER invent tables or columns that are not in the provided schema.
7. If a column or table you need is not in the schema, you cannot use it.
8. Do not access system tables unless explicitly included in the allowed schema.
9. Generate SQL compatible with PostgreSQL.
10. Return ONLY the SQL query, nothing else. No explanations, no JSON formatting.

{schema_text}

IMPORTANT: The schema above is the ONLY schema available. Do not reference any tables or columns not listed above."""

def get_gemini_service() -> GeminiService:
    """Get Gemini service instance."""
    return GeminiService()
