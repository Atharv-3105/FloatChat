from typing import List, Dict, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_service import llm_service
from app.schemas.query import QueryResponse, ChartData,MapPoint
from app.utils.cache import cache_service

class QueryService:
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        
    async def process_query(
        self,
        user_query: str,
        model_name: str = "gemini",
        max_results: int = 1000
    )-> QueryResponse:
        
        cache_key = f"query:{user_query}:{model_name}"
        cached = cache_service.get(cache_key)
        if cached:
            return QueryResponse(**cached)
        
        #Generate SQL from LLM
        sql_query, intent = llm_service.generate_sql(user_query, model_name)
        
        if not sql_query:
            return QueryResponse(
                answer = "Could not understand your query. Please rephrase.",
                chart_type=None,
                chart=None,
                map=None,
                source_info={"rows_returned": 0},
                model_used=model_name
            )
            
        #Execute the generated query
        results, columns = await self._execute_query(sql_query, max_results)
        
        if not results:
            return QueryResponse(
                answer = "No matching data found for your query",
                chart_type=None,
                chart=None,
                map=None,
                source_info={"rows_returned":0},
                model_used=model_name
            )
            
        #Format the Response 
        answer = self._generate_answer(results, columns)
        chart_data = self._prepare_chart_data(results, columns, intent)
        map_data = self._prepare_map_data(results)
        
        #Build the response
        response = QueryResponse(
            answer = answer,
            chart_type = chart_data.type if chart_data else None,
            chart=chart_data,
            map=map_data,
            table=results[:100],
            source_info={
                "rows_returned": len(results),
                "float_ids": list(set(r.get("float_id") for r in results if r.get("float_id")))[:5],
                "columns": columns
            },
            model_used=model_name
        )
        
        #Cache Response
        cache_service.set(cache_key, response.dict(), ttl=3600)
        
        return response 
    
    
    async def _execute_query(self, sql:str, max_rows:int = 1000) -> Tuple[List[Dict], List[str]]:
        
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {max_rows}"
            
        result = await self.db.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(row._mapping)  for row in result]
        
        return rows, columns
    
    def _generate_answer(self, results: List[Dict], columns: List[str]) -> str:
        
        if not results:
            return "No data found"
        
        if "temperature" in columns:
            temps = [r["temperature"] for r in results if r.get("temperature")]
            if temps:
                avg = sum(temps) / len(temps)
                return f"Found {len(results)} observations. Average temperature: {avg:.2f}°C."
        
        if "latitude" in columns and "longitude" in columns:
            unique_floats = len(set(r.get("float_id") for r in results if r.get("float_id")))
            return f"Found {len(results)} observations from {unique_floats} ARGO floats."
        
        return f"Retrieved {len(results)} records matching your query."
    
    
    #========Function to prepare the data for ChartGeneration===============
    def _prepare_chart_data(self, results: List[Dict], columns: List[str], intent: str)-> Optional[ChartData]:
        
        if intent == "depth_profile" and "pressure" in columns and "temperature" in columns:
            sorted_results = sorted(results, key = lambda x: x.get("pressure", 0))
            return ChartData(
                type = "line",
                x = [r["pressure"] for r in sorted_results],
                y = [r["temperature"] for r in sorted_results],
                x_label = "Pressure (dbar)",
                y_label = "Temperature (°C)",
                title = "Depth Profile"
            ) 
            
        return None
    
    #=========Function to prepare the data for Map Generation
    def _prepare_map_data(self, results: List[Dict]) -> Optional[List[MapPoint]]:
        
        if not results or "latitude" not in results[0]:
            return None 
        
        return [
            MapPoint(
                float_id = r.get("float_id", "unknown"),
                latitude = r["latitude"],
                longitude = r["longitude"],
                value = r.get("temperature")
            )
            for r in results[:100] if r.get("latitude") and r.get("longitude")
        ]
        
            