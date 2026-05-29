import redis
import json 
from app.config import settings  


class CacheService:
    
    def __init__(self):
        self.client = None
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_response = True)
            self.client.ping()
            print("Redis connected")
            
        except Exception as e:
            print(f"Redis unavailable: {e}")
        
    def get(self, key: str):
        if not self.client:
            return None 
        
        try:
            cached = self.client.get(f"floatchat: {key}")
            return json.loads(cached) if cached else None 
        except: 
            return None 
        
    
    def set(self, key: str, value: dict, ttl: int = 3600):
        
        if not self.client:
            return False
        
        try:
            self.client.setex(f"Floatchat:{key}", ttl, json.dums(value, default = str))
            return True
        except:
            return False
        
        
cache_service = CacheService()