import functools
import inspect # For checking async
import traceback # Added for stacktrace
from fastapi import Request, HTTPException
from starlette.responses import Response # For type hinting if result is Response
from pydantic import BaseModel # For checking schema instances

# Placeholder for where ActivityLoggerService might be globally available or how it's accessed.
# In this PoC, we will rely on it being in request.app.state.activity_logger_service

SENSITIVE_FIELD_NAMES = {'password', 'token', 'secret', 'credentials', 'cvv', 'card_number', 'api_key', 'access_token', 'refresh_token'}

def log_activity(success_event_type: str, failure_event_type: str = "GENERIC_OPERATION_FAILURE"):
    def decorator(func):
        
        def _extract_schema_data(values_dict, exclude_unset=False):
            for v in values_dict:
                if isinstance(v, BaseModel) and not isinstance(v, Request): # Ensure it's a Pydantic model and not Request
                    try:
                        return v.dict(exclude_unset=exclude_unset, exclude=SENSITIVE_FIELD_NAMES)
                    except Exception: # Fallback if exclude fails for some reason
                        return {k: val for k, val in v.dict(exclude_unset=exclude_unset).items() if k not in SENSITIVE_FIELD_NAMES}
            return None

        @functools.wraps(func)
        async def wrapper_async(*args, **kwargs):
            # Try to find Request object to access ActivityLoggerService
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            logger_service = None
            if request and hasattr(request.app.state, "activity_logger_service"):
                logger_service = request.app.state.activity_logger_service
            
            if not logger_service:
                print(f"Warning: ActivityLoggerService not found for event {success_event_type}. Operation will proceed without logging.")
                return await func(*args, **kwargs)

            event_details = {
                "event_type": success_event_type,
                "target_resource_ids": [],
                "input_args_summary": {},
                "function_name": func.__name__,
                "module_name": func.__module__,
            }

            # Attempt to get user_email from current_user if available in kwargs or args
            current_user = kwargs.get("current_user")
            if not current_user:
                for arg in args:
                    # This is a simplistic check; User model might not be directly User class
                    # and might be in args without name 'current_user'.
                    # A more robust solution would inspect type or have a convention.
                    if hasattr(arg, 'email') and hasattr(arg, 'id'): # Basic check for a user-like object
                        current_user = arg
                        break
            
            if current_user and hasattr(current_user, 'email'):
                event_details["actor_user_email"] = current_user.email
            elif current_user and hasattr(current_user, 'id'): # Fallback to user ID
                 event_details["actor_user_id"] = str(current_user.id)


            # Basic attempt to get resource ID from kwargs (common for update/delete/get_one)
            # This is very generic; specific extractors might be better.
            resource_id_keys = ["user_id", "sample_id", "role_id", "privilege_id", "id", "item_id"]
            for key in resource_id_keys:
                resource_id = kwargs.get(key)
                if resource_id:
                    event_details["target_resource_ids"].append(str(resource_id))
                    break # Found one, assuming primary target

            # Summarize kwargs (simple version, be careful with sensitive data)
            # Exclude common FastAPI/service objects and sensitive fields by default.
            excluded_keys = ['db', 'request', 'current_user', 'password', 'token', 'credentials', 'form_data']
            try:
                event_details["input_args_summary"] = {
                    k: v if len(str(v)) < 200 else str(v)[:197] + "..." # Truncate long values
                    for k, v in kwargs.items() 
                    if k not in excluded_keys and not isinstance(v, (Request, Response))
                }
            except Exception:
                event_details["input_args_summary"] = "Error summarizing kwargs"


            try:
                result = await func(*args, **kwargs)
                
                # --- Enhanced data change summary ---
                if logger_service and logger_service.config.get("LOG_DATA_MODIFICATIONS", False):
                    data_changed_summary = {}
                    input_schema_data = _extract_schema_data(kwargs.values())

                    if "CREATE" in success_event_type.upper():
                        if input_schema_data:
                            data_changed_summary["input_data"] = input_schema_data
                        if hasattr(result, 'id'):
                            data_changed_summary["created_resource_id"] = str(result.id)
                    
                    elif "UPDATE" in success_event_type.upper():
                        if event_details.get("target_resource_ids"):
                             data_changed_summary["target_resource_ids"] = event_details["target_resource_ids"]
                        update_payload_data = _extract_schema_data(kwargs.values(), exclude_unset=True)
                        if update_payload_data:
                             data_changed_summary["update_payload"] = update_payload_data
                    
                    elif "DELETE" in success_event_type.upper():
                        if event_details.get("target_resource_ids"):
                            data_changed_summary["deleted_resource_id"] = event_details["target_resource_ids"]

                    if data_changed_summary:
                        event_details["data_changed_summary"] = data_changed_summary
                # --- End of enhanced data change summary ---

                # Add result ID if not already captured as a primary target
                if hasattr(result, 'id') and str(result.id) not in event_details["target_resource_ids"]:
                     event_details["target_resource_ids"].append(f"result_id:{str(result.id)}")
                
                logger_service.log(event_details)
                return result
            except HTTPException as e:
                event_details["event_type"] = failure_event_type
                event_details["error_message"] = str(e.detail)
                event_details["status_code"] = e.status_code
                logger_service.log(event_details)
                raise
            except Exception as e:
                event_details["event_type"] = failure_event_type
                event_details["error_type"] = type(e).__name__ # Added
                event_details["error_message"] = str(e)
                event_details["error_stacktrace"] = traceback.format_exc() # Added
                logger_service.log(event_details)
                raise
        
        # Synchronous wrapper (basic, for non-async functions if needed)
        # For this PoC, the primary focus is on async FastAPI routes/services.
        # A more robust decorator might inspect `func` and provide a truly universal wrapper.
        # This synchronous part is NOT fully developed as per PoC focus on async.
        @functools.wraps(func)
        def wrapper_sync(*args, **kwargs):
            # Simplified: assumes no request object easily available for sync context unless passed explicitly
            # This part of the PoC is less critical as per instructions to focus on async.
            print(f"Warning: log_activity decorator used on synchronous function {func.__name__} without full context. Logging may be limited.")
            # Basic logging attempt without request context (logger must be globally available or passed in)
            # For now, it will likely fail to find logger_service if not passed explicitly.
            
            # This synchronous path is not fully fleshed out as per the PoC focus.
            # A real implementation would need a way to get logger_service here.
            # If we assume ActivityLoggerService is a singleton and already configured:
            try:
                from services.activity_logger_service import ActivityLoggerService
                logger_service = ActivityLoggerService() # Get singleton
            except ImportError:
                logger_service = None

            if not logger_service or not hasattr(logger_service, 'log'):
                 print(f"Warning: ActivityLoggerService not found for event {success_event_type} in sync wrapper.")
                 return func(*args, **kwargs)

            event_details = {
                "event_type": success_event_type,
                "function_name": func.__name__,
                "module_name": func.__module__,
            }
            # Limited details for sync version in this PoC
            try:
                result = func(*args, **kwargs)
                logger_service.log(event_details)
                return result
            except HTTPException as e: # Catch HTTPExceptions if they can be raised by sync services
                event_details["event_type"] = failure_event_type
                event_details["error_message"] = str(e.detail)
                event_details["status_code"] = e.status_code
                logger_service.log(event_details)
                raise
            except Exception as e:
                event_details["event_type"] = failure_event_type
                event_details["error_type"] = type(e).__name__ # Added
                event_details["error_message"] = str(e)
                event_details["error_stacktrace"] = traceback.format_exc() # Added
                logger_service.log(event_details)
                raise

        if inspect.iscoroutinefunction(func):
            return wrapper_async
        else:
            # For this PoC, the sync wrapper is very basic.
            # Consider if sync methods are a primary target for this decorator.
            # If so, it needs more robust logger access.
            # Given the focus on FastAPI, async is primary.
            # Returning the async wrapper even for sync functions might work if they are called with `await`
            # but it's not ideal. For this PoC, we'll keep it simple and focus on async.
            # The problem statement focuses on async service methods / routers.
            # So, we primarily care about `wrapper_async`.
            # If a sync function is decorated, it will use `wrapper_sync`.
            return wrapper_sync
            
    return decorator
