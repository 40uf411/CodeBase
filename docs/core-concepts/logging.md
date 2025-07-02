# Activity Logging System Documentation

## Overview

The Activity Logging System provides a comprehensive record of events occurring within the application. Its primary purposes are:

-   **Security Auditing:** Tracking significant actions, especially those related to authentication, authorization, and data modification, to identify suspicious activities or policy violations.
-   **User Activity Tracking:** Understanding how users interact with the platform, which can be valuable for support, analytics, and identifying common workflows or issues.
-   **Debugging and Troubleshooting:** Providing context for errors and unexpected behavior by logging detailed request, response, and error information.

### Key Features

-   **Admin-Configurable Logging Levels:** Specific event types can be enabled or disabled at runtime via an admin API, allowing fine-grained control over log verbosity.
-   **Detailed Request/Response Logging:** The `ActivityLoggingMiddleware` captures information for each HTTP request-response cycle, including client details, request path, and response status.
-   **Business Event Logging:** Key business logic events (e.g., user creation, resource updates) are logged using the `@log_activity` decorator or explicit service calls, providing semantic meaning to logged actions.
-   **Comprehensive Error Logging:**
    -   Unhandled exceptions are caught by the middleware and logged with stack traces.
    -   Handled exceptions (both HTTP and general) within decorated functions are also logged with relevant error details.
-   **Data Change Summaries (Optional):** When the `LOG_DATA_MODIFICATIONS` setting is enabled, logs for create, update, and delete operations can include a summary of the data that was changed (e.g., input payloads, updated fields).
-   **JSON Format:** Logs are written in JSON lines format, making them easy to parse, query, and integrate with external log management systems.

## Log Storage

-   **Format:** JSON lines (one JSON object per line).
-   **Location:** `logs/activity.log` (relative to the application root).
-   **Rotation:** Logs are rotated daily at midnight. Seven (7) backup log files are kept (e.g., `activity.log.2023-10-26`, `activity.log.2023-10-25`, etc.).
-   **Access:** Logs are stored locally on the server where the application is running. For production environments, it is highly recommended to configure log shipping to a centralized log management system (e.g., ELK Stack, Splunk, Grafana Loki, AWS CloudWatch Logs, Google Cloud Logging) for secure storage, retention, analysis, and alerting.

## Log Entry Structure (Key Fields)

While the exact fields can vary slightly based on the event type, common and important fields found in log entries include:

-   `timestamp`: (String) ISO 8601 UTC timestamp of when the log record was created (e.g., `2023-10-27T14:35:12.123456Z`).
-   `level`: (String) Log level (e.g., `INFO`, `ERROR`). Most activity logs are `INFO`; errors are `ERROR`.
-   `message`: (Object/String) The core log data. For structured logs from this system, this is typically an object containing event-specific details.
    -   `event_type`: (String) A specific identifier for the type of event being logged (e.g., `USER_LOGIN_SUCCESS`, `REQUEST_RESPONSE_CYCLE`).
    -   `user_email`: (String) Email of the authenticated user who initiated the action. Defaults to "anonymous" or "user_id:{id}" if email is not available. May also appear as `actor_user_email` in decorator logs.
    -   `request_ip_address`: (String) IP address of the client making the request (from middleware logs).
    -   `request_method`: (String) HTTP method (e.g., `GET`, `POST`) (from middleware logs).
    -   `request_path`: (String) Path of the HTTP request (e.g., `/api/v1/users/`) (from middleware logs).
    -   `response_status_code`: (Integer) HTTP status code of the response (e.g., `200`, `404`, `500`).
    -   `response_time_ms`: (Float) Time taken to process the request, in milliseconds (from middleware logs).
    -   `request_fingerprint_headers`: (Object) A collection of HTTP headers useful for client fingerprinting (e.g., `user-agent`, `referer`, `origin`). (from middleware logs).
    -   `error_message`: (String) Description of an error if one occurred.
    -   `error_type`: (String) Class name of the error (e.g., `ValueError`, `HTTPException`).
    -   `error_stacktrace`: (String) Full Python stack trace for unhandled exceptions or errors caught by the `@log_activity` decorator.
    -   `status_code`: (Integer) HTTP status code associated with an `HTTPException` when logged by the decorator.
    -   `data_changed_summary`: (Object, Optional) If `LOG_DATA_MODIFICATIONS` is enabled, this field contains details about data changes (e.g., `input_data` for creates, `update_payload` for updates). Sensitive fields are excluded.
    -   `target_resource_ids`: (List of Strings) IDs of resources affected by the operation (e.g., user ID, sample ID).
    -   `input_args_summary`: (Object) A summary of arguments passed to a decorated function (sensitive arguments excluded).
    -   `function_name`: (String) Name of the function where the event was logged (primarily from `@log_activity`).
    -   `module_name`: (String) Module where the event was logged.
-   `module`: (String) The Python module from which the log was emitted (e.g., `activity_logging_middleware`, `auth_service`).
-   `funcName`: (String) The function name from which the log was emitted.
-   `lineno`: (Integer) The line number where the log call was made.

*Note: An `event_id` (e.g., a UUID for unique log entry identification) is not explicitly part of the current default structure but could be added if needed for specific correlation requirements.*

## Configuring Logging Levels (Admin API)

The verbosity of activity logging can be controlled at runtime by enabling or disabling specific event types via an administrative API. This allows administrators to tailor logging to current needs (e.g., enabling more detailed logging during an investigation).

-   **View Current Settings:**
    -   Endpoint: `GET /api/v1/admin/logging-settings/`
    -   Method: `GET`
    -   Response: A list of all configurable logging settings and their current status (enabled/disabled) and descriptions.
      ```json
      [
        {
          "setting_name": "AUTH_LOGIN_SUCCESS",
          "is_enabled": true,
          "description": "Log successful user logins."
        },
        // ... other settings
      ]
      ```

-   **Update a Setting:**
    -   Endpoint: `PUT /api/v1/admin/logging-settings/{setting_name}`
        -   Example: `PUT /api/v1/admin/logging-settings/AUTH_LOGIN_SUCCESS`
    -   Method: `PUT`
    -   Authentication: Requires admin privileges (specifically, the `admin:logging_settings:manage` privilege).
    -   Request Body:
      ```json
      {
        "is_enabled": false
      }
      ```
    -   Response: The updated setting object.

### List of Configurable Settings

The following settings are initialized by default. Their `is_enabled` status can be modified via the admin API.

| `setting_name`             | `is_enabled` (Default) | Description                                                                          |
| -------------------------- | ---------------------- | ------------------------------------------------------------------------------------ |
| `AUTH_LOGIN_SUCCESS`       | `True`                 | Log successful user logins. (Explicitly logged in `AuthService`)                   |
| `AUTH_LOGIN_FAILURE`       | `True`                 | Log failed user login attempts. (Explicitly logged in `AuthService`)               |
| `AUTH_LOGOUT_SUCCESS`      | `True`                 | Log successful user logouts. (Example, to be implemented if logout endpoint exists)  |
| `AUTH_TOKEN_REFRESHED`     | `True`                 | Log successful token refreshes.                                                      |
| `AUTH_PASSWORD_RESET_REQUEST` | `True`                 | Log password reset requests.                                                         |
| `AUTH_PASSWORD_RESET_SUCCESS` | `True`                 | Log successful password resets.                                                      |
| `AUTH_REGISTRATION_SUCCESS` | `True`                 | Log new user registrations. (Example, depends on decorator use)                      |
| `RESOURCE_CREATE`          | `True`                 | Log creation of resources (e.g., users, roles, samples). General type.               |
| `RESOURCE_READ_ONE`        | `True`                 | Log retrieval of a single resource. General type.                                    |
| `RESOURCE_READ_LIST`       | `True`                 | Log retrieval of a list of resources. General type.                                  |
| `RESOURCE_UPDATE`          | `True`                 | Log updates to resources. General type.                                              |
| `RESOURCE_DELETE`          | `True`                 | Log deletion of resources. General type.                                             |
| `PRIVILEGE_ASSIGNED`       | `True`                 | Log assignment of privileges to roles.                                               |
| `PRIVILEGE_REMOVED`        | `True`                 | Log removal of privileges from roles.                                                |
| `ROLE_ASSIGNED_TO_USER`    | `True`                 | Log assignment of roles to users.                                                    |
| `ROLE_REMOVED_FROM_USER`   | `True`                 | Log removal of roles from users.                                                     |
| `SYSTEM_ERROR`             | `True`                 | Log unexpected system errors or exceptions. (Generic type, often for custom errors)  |
| `SECURITY_ALERT`           | `True`                 | Log potential security-related events (e.g., unauthorized access attempts).        |
| `LOG_DATA_MODIFICATIONS`   | `False`                | Log detailed data changes (input/payloads) for CUD operations. Default: False.       |
| `REQUEST_RESPONSE_CYCLE`   | `True`                 | General logging for each HTTP request-response cycle by `ActivityLoggingMiddleware`. |
| `USER_CREATE_SUCCESS`      | `True`                 | User successfully created (via decorated `AuthService.create_user`).                 |
| `USER_CREATE_FAILURE`      | `True`                 | Failed attempt to create a user (via decorated `AuthService.create_user`).           |
| `USER_CREATE_VIA_API_SUCCESS` | `True`                 | User successfully created (via decorated `user_router.create_user` API endpoint).    |
| `USER_CREATE_VIA_API_FAILURE` | `True`                 | Failed attempt to create a user (via decorated `user_router.create_user` API).       |
| `SAMPLE_CREATE_SUCCESS`    | `True`                 | Sample resource successfully created (via decorated `SampleService.create_sample`).    |
| `SAMPLE_CREATE_FAILURE`    | `True`                 | Failed attempt to create a sample (via decorated `SampleService.create_sample`).     |
| `SAMPLE_UPDATE_SUCCESS`    | `True`                 | Sample resource successfully updated (via decorated `SampleService.update_sample`).    |
| `SAMPLE_UPDATE_FAILURE`    | `True`                 | Failed attempt to update a sample (via decorated `SampleService.update_sample`).     |
| `SAMPLE_CREATE_VIA_API_SUCCESS` | `True`               | Sample successfully created (via decorated `sample_router.create_sample` API).       |
| `SAMPLE_CREATE_VIA_API_FAILURE` | `True`               | Failed attempt to create a sample (via decorated `sample_router.create_sample` API). |
| `SAMPLE_UPDATE_VIA_API_SUCCESS` | `True`               | Sample successfully updated (via decorated `sample_router.update_sample` API).       |
| `SAMPLE_UPDATE_VIA_API_FAILURE` | `True`               | Failed attempt to update a sample (via decorated `sample_router.update_sample` API). |
| `GENERIC_OPERATION_FAILURE`| `True`                 | Default failure event type for `@log_activity` if specific one not provided.         |
| `UNHANDLED_EXCEPTION`      | `True`                 | An unhandled exception was caught by the `ActivityLoggingMiddleware`.                |

*Note: The specific `event_type` strings used by the `@log_activity` decorator are defined when the decorator is applied to a function (e.g., `USER_CREATE_SUCCESS`). The table above includes examples based on the current implementation.*

## Key Event Types (`event_type` values)

These are some of the most important `event_type` values you might encounter in the logs:

-   **`REQUEST_RESPONSE_CYCLE`**: Logged by the `ActivityLoggingMiddleware` for every processed HTTP request. Provides general request/response metadata.
-   **`UNHANDLED_EXCEPTION`**: Logged by the `ActivityLoggingMiddleware` when an unexpected error occurs that is not caught by more specific error handlers. Includes stack trace.
-   **`USER_LOGIN_SUCCESS`**: User successfully authenticated.
-   **`USER_LOGIN_FAILURE`**: Failed login attempt.
-   **`USER_CREATE_SUCCESS` / `USER_CREATE_VIA_API_SUCCESS`**: A new user account was successfully created. The `_VIA_API_` variant distinguishes router-level logs from service-level.
-   **`USER_CREATE_FAILURE` / `USER_CREATE_VIA_API_FAILURE`**: An attempt to create a new user account failed.
-   **`SAMPLE_CREATE_SUCCESS` / `SAMPLE_CREATE_VIA_API_SUCCESS`**: A sample resource was created.
-   **`SAMPLE_UPDATE_SUCCESS` / `SAMPLE_UPDATE_VIA_API_SUCCESS`**: A sample resource was updated.
-   **`[RESOURCE_TYPE]_[ACTION]_SUCCESS/FAILURE`**: General pattern for other decorated operations.
-   **`GENERIC_OPERATION_FAILURE`**: Default failure event type used by the `@log_activity` decorator if a more specific one isn't provided.

## Security and Privacy

-   **`LOG_DATA_MODIFICATIONS` Setting:**
    -   Enabling the `LOG_DATA_MODIFICATIONS` setting provides a detailed audit trail of data changes, which can be very useful. However, it also increases log verbosity and means that parts of the input data or update payloads will be written to the logs.
    -   The system attempts to automatically exclude common sensitive fields (e.g., `password`, `token`, `secret_key`) from the `data_changed_summary`.
    -   **Action Required:** If your Pydantic models contain other fields with sensitive information not covered by the default exclusion list, you should review the `SENSITIVE_FIELD_NAMES` set in `utils/activity_logging_decorators.py` and extend it as necessary, or implement more sophisticated data masking if required.
-   **Log Access Control:**
    -   Ensure that access to log files (e.g., `logs/activity.log`) and any centralized log management system is strictly restricted to authorized personnel. Log data can contain sensitive operational details and potentially user information.
-   **Regular Review:** Periodically review log configurations and logged data to ensure they align with your security and privacy policies.

## Development Notes

-   **Adding New Loggable Events:**
    -   **For service methods or router functions:** The easiest way is to apply the `@log_activity(success_event_type="YOUR_EVENT_SUCCESS", failure_event_type="YOUR_EVENT_FAILURE")` decorator. Ensure the function is `async` and can accept `request: Request` as a parameter (or that `request` is available in its `args`/`kwargs`).
    -   **For explicit logging within functions:** Obtain an instance of `ActivityLoggerService` (usually via `request.app.state.activity_logger_service`) and call its `log()` method with a dictionary containing at least an `event_type` key and other relevant details.
    -   Remember to define new `setting_name`s for your new `event_type`s in `AdminLoggingSettingService.initialize_default_settings()` if you want them to be configurable via the admin API.
-   **Core Components:**
    -   **`ActivityLoggerService` (`services/activity_logger_service.py`):** The core singleton service that handles log formatting, file output, and conditional logging based on admin-configured settings.
    -   **`@log_activity` decorator (`utils/activity_logging_decorators.py`):** A convenient way to wrap functions and automatically log their execution success/failure along with contextual data.
    -   **`ActivityLoggingMiddleware` (`middleware/activity_logging_middleware.py`):** Intercepts all requests to log general request/response cycle information and unhandled exceptions.

This documentation provides a guide to understanding, configuring, and utilizing the activity logging system.
