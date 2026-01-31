from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging
from dotenv import load_dotenv
from app.ai_agent import AIAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Shopify Analytics Service", version="1.0.0")

# Initialize AI agent
ai_agent = AIAgent()

# Get configuration from environment
AI_SERVICE_HOST = os.getenv("HOST", "0.0.0.0")
AI_SERVICE_PORT = int(os.getenv("PORT", 8000))
AI_SERVICE_DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Request model


class QuestionRequest(BaseModel):
    question: str
    store_id: str
    shop_access_token: Optional[str] = None

# Response model


class QuestionResponse(BaseModel):
    answer: str
    confidence: str
    query_used: Optional[str] = None
    data_summary: Optional[dict] = None


@app.get("/")
async def root():
    return {"message": "AI Shopify Analytics Service", "status": "running"}


@app.post("/api/v1/process-question", response_model=QuestionResponse)
async def process_question(request: QuestionRequest):
    """
    Process a natural language question and return an answer
    """
    try:
        logger.info(
            f"Processing question: {request.question} for store: {request.store_id}")

        if not request.shop_access_token:
            raise HTTPException(
                status_code=400, detail="Shop access token is required")

        # Process question with AI agent
        result = await ai_agent.process_question(
            request.question,
            request.store_id,
            request.shop_access_token
        )

        return QuestionResponse(**result)
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Shopify Analytics Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=AI_SERVICE_HOST,
        port=AI_SERVICE_PORT,
        reload=AI_SERVICE_DEBUG
    )
