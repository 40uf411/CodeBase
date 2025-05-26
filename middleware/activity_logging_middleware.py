import json
import time
import traceback # Added for stacktrace
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCallNext
from starlette.requests import Request
from starlette.responses import Response, JSONResponse # Added JSONResponse
from fastapi import HTTPException # Added to specifically catch and re-raise
from services.activity_logger_service import ActivityLoggerService

class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Initialize the logger service.
        # Log file path can be configured here or in ActivityLoggerService itself.
        self.logger_service = ActivityLoggerService()

    async def dispatch(self, request: Request, call_next: RequestResponseCallNext) -> Response:
        start_time = time.perf_counter()

        # Basic request info
        request_ip_address = request.client.host if request.client else "unknown"
        request_method = request.method
        request_path = request.url.path

        # Expanded fingerprinting headers
        headers_to_log_keys = [
            "user-agent", "referer", "origin", "accept-language",
            "accept-encoding", "accept", "x-forwarded-for", "x-real-ip"
        ]
        request_fingerprint_headers = {
            key: request.headers.get(key, "unknown") for key in headers_to_log_keys
        }
        
        user_email = "anonymous" # Default before trying to get from request.state

        try:
            # Process the request
            response = await call_next(request)
            end_time = time.perf_counter()
            response_time_ms = round((end_time - start_time) * 1000, 2)
            response_status_code = response.status_code

            # User info might be set by other middleware/dependencies after call_next
            if hasattr(request.state, "user") and request.state.user and hasattr(request.state.user, "email"):
                user_email = request.state.user.email
            elif hasattr(request.state, "user") and request.state.user and hasattr(request.state.user, "id"):
                user_email = f"user_id:{request.state.user.id}"

            log_data = {
                "event_type": "REQUEST_RESPONSE_CYCLE",
                "user_email": user_email,
                "request_ip_address": request_ip_address,
                "request_method": request_method,
                "request_path": request_path,
                "request_fingerprint_headers": request_fingerprint_headers, # Added
                "response_status_code": response_status_code,
                "response_time_ms": response_time_ms,
            }
            self.logger_service.log(log_data)
            return response

        except HTTPException as e:
            # HTTPExceptions are typically handled by FastAPI's own error handling.
            # Re-raise to let FastAPI process it into a standard HTTP response.
            # If specific logging for HTTPExceptions is desired here, it can be added,
            # but often it's better handled by the decorator for business logic exceptions.
            raise e 
        
        except Exception as e:
            end_time = time.perf_counter() # Record time even for errors
            response_time_ms = round((end_time - start_time) * 1000, 2)

            # Attempt to get user info if available at point of exception
            if hasattr(request.state, "user") and request.state.user and hasattr(request.state.user, "email"):
                user_email = request.state.user.email
            elif hasattr(request.state, "user") and request.state.user and hasattr(request.state.user, "id"):
                 user_email = f"user_id:{request.state.user.id}"

            error_log_data = {
                "event_type": "UNHANDLED_EXCEPTION",
                "user_email": user_email,
                "request_ip_address": request_ip_address,
                "request_method": request_method,
                "request_path": request_path,
                "request_fingerprint_headers": request_fingerprint_headers, # Added
                "response_status_code": 500,
                "response_time_ms": response_time_ms, # Time until error
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_stacktrace": traceback.format_exc(),
            }
            try:
                self.logger_service.log(error_log_data)
            except Exception as log_exc:
                 print(f"CRITICAL: Failed to log UNHANDLED_EXCEPTION: {log_exc}, Original error: {e}, Log data: {str(error_log_data)}")
            
            # Return a generic 500 response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )
