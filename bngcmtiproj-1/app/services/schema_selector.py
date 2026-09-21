from typing import Set, Dict, List
import logging
from sqlalchemy import inspect
from app.db.session import engine

logger = logging.getLogger(__name__)

# Keywords for table matching (table_name -> keywords)
TABLE_KEYWORDS = {
    "users": ["user", "users", "operator", "operators", "officer", "officers", "supervisor", "supervisors", "person", "people", "employee", "employees"],
    "tool_inventory": ["tool", "tools", "inventory", "gauge", "gauges", "item", "items", "equipment", "stock", "available", "quantity", "hammer", "hammer", "drill", "screwdriver", "wrench", "plier", "saw", "measure", "caliper", "micrometer", "vernier", "tap", "die", "cutter", "grinder", "file", "chisel", "punch", "reamer", "bore", "lathe", "mill", "shaper", "slotter", "planer", "hob", "broach", "laser", "cnc", "machine"],
    "tool_issues": ["issue", "issues", "problem", "problems", "maintenance", "repair", "broken", "damaged", "defective", "faulty"],
    "tool_usage_requests": ["request", "requests", "usage", "used", "borrow", "borrowed", "issue", "issued", "checkout", "checked out"],
    "tool_addition_requests": ["addition", "add", "new", "addition request", "new tool", "purchase", "order"],
    "sessions": ["session", "sessions", "login", "logins", "logout", "logouts", "active", "logged in"],
    "role_locks": ["lock", "locks", "role", "role lock"],
    "notifications": ["notification", "notifications", "alert", "alerts", "message", "messages"]
}

class SchemaSelector:
    def __init__(self):
        self.schema = self._fetch_schema_from_db()
        self.keywords = TABLE_KEYWORDS

    def _fetch_schema_from_db(self) -> Dict[str, List[str]]:
        """
        Dynamically fetch database schema from the actual database.
        
        Returns:
            Dictionary mapping table names to their column names
        """
        try:
            inspector = inspect(engine)
            schema = {}
            
            # Get all table names
            table_names = inspector.get_table_names()
            logger.info(f"Found {len(table_names)} tables in database: {table_names}")
            
            # Get columns for each table
            for table_name in table_names:
                columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in columns]
                schema[table_name] = column_names
                logger.info(f"Table '{table_name}' has columns: {column_names}")
            
            return schema
        except Exception as e:
            logger.error(f"Error fetching schema from database: {e}")
            # Fallback to empty schema
            return {}

    def get_relevant_schema(self, question: str) -> Dict[str, List[str]]:
        """
        Determine which tables and columns are relevant to the question.
        
        Args:
            question: Natural language question
        
        Returns:
            Dictionary mapping table names to their relevant columns
        """
        question_lower = question.lower()
        relevant_tables = {}
        
        # Score each table based on keyword matches
        table_scores = {}
        for table_name, columns in self.schema.items():
            score = 0
            matched_keywords = []
            
            # Get keywords for this table (if defined)
            table_keywords = self.keywords.get(table_name, [])
            
            for keyword in table_keywords:
                if keyword in question_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                table_scores[table_name] = (score, matched_keywords)
        
        # Sort by score and take top tables
        sorted_tables = sorted(table_scores.items(), key=lambda x: x[1][0], reverse=True)
        
        # Include top 3 tables (or all if fewer)
        for table_name, (score, keywords) in sorted_tables[:3]:
            relevant_tables[table_name] = self.schema[table_name]
            logger.info(f"Selected table '{table_name}' with keywords: {keywords}")
        
        # If no tables matched, return all tables (fallback)
        if not relevant_tables:
            logger.warning("No relevant tables found, returning all tables")
            for table_name, columns in self.schema.items():
                relevant_tables[table_name] = columns
        
        return relevant_tables

    def get_all_tables(self) -> Set[str]:
        """Get all table names."""
        return set(self.schema.keys())

    def get_table_columns(self, table_name: str) -> List[str]:
        """Get columns for a specific table."""
        if table_name in self.schema:
            return self.schema[table_name]["columns"]
        return []

    def format_schema_for_prompt(self, schema: Dict[str, List[str]]) -> str:
        """
        Format schema for inclusion in OpenAI prompt.
        
        Args:
            schema: Dictionary mapping table names to columns
        
        Returns:
            Formatted schema string
        """
        lines = ["Database Schema:"]
        for table_name, columns in schema.items():
            lines.append(f"Table: {table_name}")
            lines.append(f"  Columns: {', '.join(columns)}")
        return "\n".join(lines)

def get_relevant_schema(question: str) -> Dict[str, List[str]]:
    """
    Get relevant schema for a natural language question.
    
    Args:
        question: Natural language question
    
    Returns:
        Dictionary mapping table names to their relevant columns
    """
    selector = SchemaSelector()
    return selector.get_relevant_schema(question)
