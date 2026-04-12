import re 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.config import settings 

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
1. SELECT queries only (READ-ONLY)
2. Filter: temperature BETWEEN -5 AND 40
3. Filter: pressure BETWEEN 0 AND 7000
4. Include float_id for citation
"""

PROMPT = f"""
You are an oceanographic data expert. Convert the question to SQLite SQL.

{DB_SCHEMA}

Examples:
Q: "Show temperature at 500m depth"
A: SELECT float_id, pressure, temperature FROM argo_data WHERE pressure BETWEEN 450 AND 550 LIMIT 1000

Q: "What floats was near Mumbai?"
A: SELECT DISTINCT float_id, latitude, longitude FROM argo_data WHERE latitude BETWEEN 18 AND 20 AND longitude BETWEEN 72 AND 74

Question: {{user_query}}

SQL:

"""


#========Class which will handle the LLM operations for Query Processing
class LLMService:
    
    def __init__(self):
        self.models = {}
    
    def _get_model(self, model_name: str):
        
        if model_name not in self.models:
            if model_name == "gemini":
                self.models[model_name] = ChatGoogleGenerativeAI(
                    model = "gemini-2.5-flash",
                    google_api_key = settings.GEMINI_API_KEY,
                    temperature = 0.1
                )
            elif model_name == "gpt":
                self.models[model_name] = ChatOpenAI(
                    model = "gpt-3.5",
                    openai_api_key = settings.OPENAI_API_KEY,
                    temperature = 0.1
                )
        
        return self.models.get(model_name)
    
    
    def generate_sql(self, user_query: str, model_name: str = "gemini"):
        ''' 
            Function to generate SQL from natural language query
        '''
        
        try:
            model = self._get_model(model_name)
            if not model:
                return None, "unknown"
            
            prompt = PROMPT.format(user_query = user_query)
            response = model.invoke(prompt)
            
            #Extract SQL from the response
            sql = self._extract_sql(response.content)
            
            #Validate the Extracted SQL
            if not self._validate_sql(sql):
                return None, "unknown"
            
            #Classify the intent in the Query
            intent = self._classify_intent(user_query)
            
            return sql, intent 
        
        except Exception as e:
            print(f"LLM Error: {e}")
            return None, "unknown"
        
    def _extract_sql(self, response: str) -> str:
        import re 
        match = re.search(r'```sql\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        #Find SELECT in response
        match = re.search(r'(SELECT.*?;?)', response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return response.strip()
    
    
    def _validate_sql(self, sql: str) -> bool:
        ''' 
            Return TRUE if SELECT is in SQL
        '''
        if not sql:
            return False 
        
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith("SELECT"):
            return False 
        
        #Block Some Keywords
        keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]
        for keyword in keywords:
            if keyword in sql_upper:
                return False 
            
        return True 
    
    def _classify_intent(self, query: str) ->str:
        
        query_lower = query.lower()
        
        if any(w in query_lower for w in ["profile", "depth", "pressure"]):
            return "depth_profile"
        elif any(w in query_lower for w in ["map", "location", "where"]):
            return "map"
        elif any(w in query_lower for w in ["compare", "between"]):
            return "comparison"
        else:
            return "table"
        
        
        

llm_service = LLMService()