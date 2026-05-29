import re
import json
from typing import List, Dict, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_service import llm_service
from app.schemas.query import QueryResponse, ChartData, MapPoint
from app.utils.cache import cache_service
from app.exceptions import LLMError, SQLGenerationError, HTTPException
from app.logging_config import logger

class QueryService:

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def process_query(
        self,
        user_query: str,
        model_name: str = "gemini",
        max_results: int = 1000
    ) -> QueryResponse:
        """
        Processes a query and returns the full response.
        """
        try:
            # Step 1: Check cache
            cache_key = f"query:{user_query}:{model_name}"
            cached = cache_service.get(cache_key)
            if cached:
                return QueryResponse(**cached)

            # Step 2: Generate SQL
            sql_query, intent = await llm_service.generate_sql(user_query, model_name)

            # Step 3: Execute Query
            results, columns = await self._execute_query(sql_query, max_results)

            # Step 4: Expand search if no results
            if not results:
                expanded_results = await self._expand_search_and_retry(sql_query, max_results)
                if expanded_results:
                    results, columns, sql_query = expanded_results
                else:
                    return QueryResponse(
                        answer="No matching data found, even after expanding the search area.",
                        source_info={"rows_returned": 0},
                        model_used=model_name
                    )
            
            # Step 5: Summarize results
            answer = await llm_service.summarize_data(
                user_query=user_query,
                data_sample=results[:10],
                model_name=model_name
            )

            # Step 6: Prepare visualizations and build final response
            chart_data = self._prepare_chart_data(results, columns, intent)
            map_data = self._prepare_map_data(results)

            response = QueryResponse(
                answer=answer,
                chart_type=chart_data.type if chart_data else None,
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

            # Step 7: Cache and return
            cache_service.set(cache_key, response.dict(), ttl=3600)
            return response

        except (SQLGenerationError, LLMError) as e:
            logger.warning(f"Handled query error: {e}")
            if isinstance(e, LLMError):
                raise HTTPException(status_code=503, detail="The language model service is currently unavailable.")
            raise HTTPException(status_code=400, detail="Could not understand your query. Please try rephrasing.")

        except Exception as e:
            logger.error(f"An unexpected error occurred in query processing: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An internal server error occurred.")

    async def _expand_search_and_retry(self, sql: str, max_rows: int) -> Optional[Tuple[List[Dict], List[str], str]]:
        lat_pattern = re.compile(r"(latitude\s+BETWEEN\s+)([\d\.\-]+)(\s+AND\s+)([\d\.\-]+)", re.IGNORECASE)
        lon_pattern = re.compile(r"(longitude\s+BETWEEN\s+)([\d\.\-]+)(\s+AND\s+)([\d\.\-]+)", re.IGNORECASE)
        lat_match = lat_pattern.search(sql)
        lon_match = lon_pattern.search(sql)
        if not lat_match or not lon_match:
            return None
        lat_min_orig, lat_max_orig = float(lat_match.group(2)), float(lat_match.group(4))
        lon_min_orig, lon_max_orig = float(lon_match.group(2)), float(lon_match.group(4))
        expansion_levels = [5, 10, 20]
        for level in expansion_levels:
            lat_center, lon_center = (lat_min_orig + lat_max_orig) / 2, (lon_min_orig + lon_max_orig) / 2
            lat_min_new, lat_max_new = lat_center - level / 2, lat_center + level / 2
            lon_min_new, lon_max_new = lon_center - level / 2, lon_center + level / 2
            new_sql = lat_pattern.sub(rf"\g<1>{lat_min_new}\g<3>{lat_max_new}", sql)
            new_sql = lon_pattern.sub(rf"\g<1>{lon_min_new}\g<3>{lon_max_new}", new_sql)
            results, columns = await self._execute_query(new_sql, max_rows)
            if results:
                return results, columns, new_sql
        return None

    async def _execute_query(self, sql:str, max_rows:int = 1000) -> Tuple[List[Dict], List[str]]:
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')}" + " LIMIT " + f"{max_rows}"
        result = await self.db.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(row._mapping) for row in result]
        return rows, columns

    def _prepare_chart_data(self, results: List[Dict], columns: List[str], intent: str)-> Optional[ChartData]:
        if intent == "depth_profile" and "pressure" in columns and "temperature" in columns:
            sorted_results = sorted(results, key=lambda x: x.get("pressure", 0))
            return ChartData(
                type="line",
                x=[r["pressure"] for r in sorted_results],
                y=[r["temperature"] for r in sorted_results],
                ids=[r.get("float_id") for r in sorted_results],
                x_label="Pressure (dbar)",
                y_label="Temperature (°C)",
                title="Depth Profile"
            )
        return None

    def _prepare_map_data(self, results: List[Dict]) -> Optional[List[MapPoint]]:
        if not results or "latitude" not in results[0]:
            return None
        return [MapPoint(float_id=r.get("float_id", "unknown"), latitude=r["latitude"], longitude=r["longitude"], value=r.get("temperature")) for r in results[:100] if r.get("latitude") and r.get("longitude")]
