class LLMError(Exception):
    """Custom exception for errors related to the LLM service."""
    pass

class SQLGenerationError(Exception):
    """Custom exception for errors during SQL generation or validation."""
    pass

class HTTPException(Exception):
    pass