from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio
import logging

logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout=60):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            # Set timeout for the request
            response = await asyncio.wait_for(call_next(request), timeout=self.timeout)
            return response
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {request.url.path}")
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )
        except asyncio.CancelledError:
            logger.error(f"Request cancelled for {request.url.path}")
            return JSONResponse(
                status_code=499,
                content={"detail": "Client closed request"}
            )
        except Exception as e:
            logger.error(f"Error processing request {request.url.path}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            ) 