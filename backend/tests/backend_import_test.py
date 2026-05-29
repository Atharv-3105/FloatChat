import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("🧪 Testing Imports...")
print("=" * 50)

try:
    from app.utils.cache import cache_service
    print("✅ cache_service imported successfully")
    print(f"   Redis client: {'Connected' if cache_service.client else 'Not available'}")
except Exception as e:
    print(f"❌ cache_service import failed: {e}")

try:
    from app.services.query_service import QueryService
    print("✅ QueryService imported successfully")
except Exception as e:
    print(f"❌ QueryService import failed: {e}")

try:
    from app.services.llm_service import llm_service
    print("✅ llm_service imported successfully")
except Exception as e:
    print(f"❌ llm_service import failed: {e}")

print("=" * 50)
print("✅ Import test complete!\n")