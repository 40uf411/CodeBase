# OAuth 2.0 Integration

This document describes the OAuth 2.0 integration within the application, allowing users to authenticate using third-party identity providers.

## Introduction to OAuth 2.0

OAuth 2.0 is an open standard for access delegation, commonly used as a way for users to grant websites or applications access to their information on other websites but without giving them the passwords. In this application, OAuth 2.0 is primarily used for authentication, enabling users to sign up or log in using their existing accounts with supported third-party providers. This simplifies the registration process and means users don't have to remember another password.

## Supported OAuth Providers

Currently, the application supports authentication via the following OAuth 2.0 providers:

- **Google**
- **GitHub**
- *(Potentially others, this list should be updated as more providers are added, e.g., Facebook, LinkedIn, etc.)*

## OAuth Flow: Authorization Code Grant

The application implements the **Authorization Code Grant** flow, which is considered one of the most secure OAuth 2.0 flows and is suitable for server-side applications. The steps involved are:

1.  **User Initiates Login:** The user clicks a "Login with [Provider]" button in the application.
2.  **Redirect to Provider:** The application redirects the user's browser to the OAuth provider's authorization server (e.g., Google's login page). This request includes the application's `client_id`, requested `scopes` (permissions), a `redirect_uri`, and a `state` parameter (for CSRF protection).
3.  **User Authenticates and Authorizes:** The user authenticates with the provider (if not already logged in) and grants the application permission to access the requested information.
4.  **Provider Redirects with Authorization Code:** If authorization is successful, the provider redirects the user's browser back to the `redirect_uri` specified by the application. This redirect includes an `authorization_code` and the `state` parameter.
5.  **Application Verifies State and Exchanges Code for Tokens:**
    *   The application first verifies that the received `state` parameter matches the one generated initially to prevent CSRF attacks.
    *   The application then sends a request directly to the provider's token endpoint (not via the user's browser). This request includes the `authorization_code`, `client_id`, `client_secret`, and `redirect_uri`.
6.  **Provider Issues Tokens:** If the request is valid, the provider returns an `access_token`, an `id_token` (if OpenID Connect is used, common with Google), and optionally a `refresh_token`.
7.  **Application Retrieves User Information:** The application uses the `access_token` (or decodes the `id_token`) to request user information (e.g., email, name, profile picture) from the provider's user info endpoint.
8.  **User Authentication/Registration in Application:**
    *   The application checks if a user with the retrieved email address already exists in its database.
    *   If the user exists, they are logged in.
    *   If the user does not exist, a new user account is created with the information from the provider, and then the user is logged in.
9.  **Session Created:** A session is established for the user in the application.

## Configuration for Each Provider

To enable OAuth providers, you need to register your application with each provider to obtain a Client ID and Client Secret. These credentials, along with the Redirect URI(s), must be configured in the application, typically via environment variables.

**Common Environment Variables:**

-   **Google:**
    -   `GOOGLE_CLIENT_ID`: Your Google application's Client ID.
    -   `GOOGLE_CLIENT_SECRET`: Your Google application's Client Secret.
    -   `GOOGLE_REDIRECT_URI`: The URI in your application where Google will redirect users after authentication (e.g., `https://yourdomain.com/auth/google/callback`).
-   **GitHub:**
    -   `GITHUB_CLIENT_ID`: Your GitHub application's Client ID.
    -   `GITHUB_CLIENT_SECRET`: Your GitHub application's Client Secret.
    -   `GITHUB_REDIRECT_URI`: The URI in your application where GitHub will redirect users (e.g., `https://yourdomain.com/auth/github/callback`).

*Note: The exact names of these environment variables might differ based on the project's specific configuration. Always refer to the `.env.example` or deployment guide.*

**Redirect URIs:** When registering your application with the provider, you must specify one or more Redirect URIs. These URIs must exactly match what your application sends and what is configured in the environment variables. For security, providers only redirect to pre-registered URIs.

## Enabling/Disabling OAuth Providers

OAuth providers can typically be enabled or disabled based on the presence of their respective environment variables for Client ID and Client Secret. If the required variables for a provider are not set, that provider's login option might not be displayed or will be non-functional.

*(Project-specific: There might be additional feature flags or configuration settings in a file like `config/settings.py` or `core/config.py` to explicitly enable/disable providers.)*

## User Information Mapping

When user information is fetched from an OAuth provider, it needs to be mapped to the application's user model (e.g., `models.User`). This usually involves:

-   **Email:** The email address is typically used as the primary identifier to link or create an application user.
-   **Name/Username:** The provider's display name or username might be used to populate the user's profile.
-   **Profile Picture:** A URL to the user's profile picture might be stored.

The application should handle cases where some information is not provided by the OAuth provider or not requested due to scope limitations. A unique identifier from the provider (e.g., Google's `sub` claim) might also be stored to link the application user account to the external provider account.

## Security Considerations

-   **Storing Tokens Securely:**
    -   `access_token` and `refresh_token` obtained from providers should be stored securely. For server-side applications, this often means encrypting them before storing them in the database, especially if they are long-lived.
    -   Avoid exposing these tokens to the client-side (browser) unless absolutely necessary and if using flows designed for public clients (like SPA with PKCE). For the Authorization Code Grant, tokens are primarily handled server-side.
-   **State Parameter:** The `state` parameter is crucial for preventing Cross-Site Request Forgery (CSRF) attacks. It should be a unique, non-guessable value generated by the application before redirecting to the provider and validated when the provider redirects back.
-   **PKCE (Proof Key for Code Exchange):** While originally designed for public clients (like mobile or SPAs), PKCE can also be used by confidential clients (like our server-side app) to further enhance security by preventing authorization code interception attacks. *(Project-specific: Mention if PKCE is implemented).*
-   **HTTPS:** All communications, especially the `redirect_uri`, must use HTTPS to protect sensitive data like authorization codes and tokens in transit.
-   **Scope Minimization:** Only request the minimum necessary `scopes` (permissions) from the user.
-   **Token Expiration and Refresh:** Handle `access_token` expiration by using `refresh_token` (if available and stored) to obtain new access tokens without requiring the user to re-authenticate.
-   **Secure Client Secret Handling:** The `client_secret` must be kept confidential and stored securely on the server. It should never be exposed in client-side code.

## Relevant Files/Modules

The implementation of OAuth functionality is typically found in:

-   **Routers:** Specific route handlers for initiating the OAuth flow and handling the callback from the provider. For example:
    -   `routers/auth.py` or `routers/oauth.py` might contain routes like `/login/google`, `/auth/google/callback`.
-   **Services/Logic:** Modules responsible for the core logic of communicating with OAuth providers, exchanging codes for tokens, fetching user info, and creating/updating user accounts. For example:
    -   `services/oauth_service.py`
    -   `core/oauth_clients.py` (containing specific client logic for Google, GitHub, etc.)
-   **Configuration:**
    -   `core/config.py` for loading OAuth-related environment variables.
    -   Potentially Pydantic models for OAuth settings.

*(This section should be updated with actual file paths and module names from the project.)*

## How to Add a New OAuth Provider

Adding a new OAuth provider generally involves the following steps:

1.  **Register Application with Provider:** Go to the new provider's developer portal and register your application. Obtain a Client ID and Client Secret. Configure the allowed Redirect URIs.
2.  **Configuration:** Add new environment variables for the new provider's Client ID, Client Secret, and Redirect URI (e.g., `NEWPROVIDER_CLIENT_ID`, `NEWPROVIDER_CLIENT_SECRET`). Update configuration loading logic if necessary.
3.  **Client Logic:**
    -   Implement the necessary functions/methods to interact with the new provider's authorization server and token endpoint. This includes constructing the authorization URL, exchanging the code for tokens, and fetching user information. Many libraries (e.g., `httpx-oauth`, `Authlib`) can simplify this.
    -   Add a new client class or functions in the OAuth services module (e.g., in `core/oauth_clients.py` or `services/oauth_service.py`).
4.  **Routes:**
    -   Add new API routes for initiating login with the new provider (e.g., `/login/newprovider`) and for handling the callback (e.g., `/auth/newprovider/callback`).
5.  **User Interface:** Add a "Login with [NewProvider]" button or link to the frontend.
6.  **User Mapping:** Ensure the user information retrieved from the new provider is correctly mapped to your application's user model.
7.  **Documentation:** Update this documentation and any relevant user guides.
8.  **Testing:** Thoroughly test the new provider integration, including successful login, registration, and error handling.

Consider using a generic OAuth client library or extending an existing abstract OAuth client class within the project to minimize code duplication when adding new providers.

---

*This document provides a general overview. For specific implementation details, always refer to the source code and project-specific configuration guides.*
