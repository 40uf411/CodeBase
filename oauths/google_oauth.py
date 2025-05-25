from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from core.database import get_db
from core.config import settings
from services.auth_service import AuthService

# OAuth setup
config = Config(environ={
    'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID,
    'GOOGLE_CLIENT_SECRET': settings.GOOGLE_CLIENT_SECRET,
})

oauth = OAuth(config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

class GoogleOAuth:
    """
    Google OAuth integration for authentication.
    
    Features:
    - OAuth2 login flow
    - User registration with Google account
    - Token management
    - Session handling
    """
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize OAuth with FastAPI app.
        
        Args:
            app: FastAPI application
        """
        # Add session middleware
        app.add_middleware(SessionMiddleware, secret_key=settings.GOOGLE_SECRET_KEY)
        
        # Create router
        router = APIRouter(prefix="/auth/google", tags=["google_auth"])
        
        @router.get("/login")
        async def login(request: Request):
            """
            Initiate Google OAuth login flow.
            """
            redirect_uri = request.url_for('auth')
            return await oauth.google.authorize_redirect(request, redirect_uri)
        
        @router.get("/auth")
        async def auth(request: Request, db: Session = Depends(get_db)):
            """
            Handle OAuth callback and authenticate user.
            """
            try:
                token = await oauth.google.authorize_access_token(request)
                user_info = await oauth.google.parse_id_token(request, token)
                
                # Get or create user
                auth_service = AuthService(db)
                user = auth_service.get_or_create_oauth_user(
                    email=user_info['email'],
                    full_name=user_info.get('name', ''),
                    oauth_provider='google',
                    oauth_id=user_info['sub']
                )
                
                # Create JWT tokens
                tokens = auth_service.create_tokens(user.id)
                
                # Store tokens in session
                request.session['access_token'] = tokens['access_token']
                request.session['refresh_token'] = tokens['refresh_token']
                
                # Redirect to frontend with tokens
                frontend_url = settings.FRONTEND_URL or "/"
                redirect_url = f"{frontend_url}?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
                return RedirectResponse(url=redirect_url)
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authentication failed: {str(e)}",
                )
        
        # Include router in app
        app.include_router(router)
    
    @staticmethod
    def get_current_user_from_session(request: Request, db: Session = Depends(get_db)):
        """
        Get current user from session.
        
        Args:
            request: FastAPI request
            db: Database session
            
        Returns:
            User object if authenticated
            
        Raises:
            HTTPException: If authentication fails
        """
        access_token = request.session.get('access_token')
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        auth_service = AuthService(db)
        return auth_service.get_current_user(access_token)
