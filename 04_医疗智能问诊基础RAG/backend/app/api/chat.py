"""
Chat API routes: /api/chat and /api/chat/stream (SSE).
"""

import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, SourceItem
from app.core.rag import generate_answer, generate_answer_stream

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint: retrieve relevant knowledge chunks and generate answer.
    Returns answer, source documents, and confidence score.
    """
    try:
        result = generate_answer(request.question, request.top_k)
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceItem(**s) for s in result["sources"]],
            confidence=result["confidence"],
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    Events: sources, chunk, done.
    """
    async def event_generator():
        try:
            async for event in generate_answer_stream(request.question, request.top_k):
                event_type = event["type"]
                data = json.dumps(event["data"], ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = json.dumps({"content": f"Error: {str(e)}"}, ensure_ascii=False)
            yield f"event: chunk\ndata: {error_data}\n\n"
            yield f"event: done\ndata: {{}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
