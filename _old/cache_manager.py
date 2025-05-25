from typing import Dict, List, Optional, Callable, Any
from fastapi import FastAPI
import redis

from core.config import settings
from .system import CacheSystem, CacheMiddleware

class CacheManager:
    """
    Manager for configuring and initializing the caching system.
    
    Features:
    - Initialize Redis connection
    - Configure cache middleware
    - Manage cache configurations
    """
    
    def __init__(self, app: Optional[FastAPI] = None):
        """
        Initialize the cache manager.
        
        Args:
            app: FastAPI application
        """
        self.redis_client = redis.Redis(
            host=settings.DRAGONFLY_HOST,
            port=settings.DRAGONFLY_PORT,
            db=settings.DRAGONFLY_DB,
            password=settings.DRAGONFLY_PASSWORD,
            decode_responses=False
        )
        
        self.cache_system = CacheSystem(self.redis_client)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: FastAPI) -> None:
        """
        Initialize caching with FastAPI app.
        
        Args:
            app: FastAPI application
        """
        # Add cache system to app state
        app.state.cache_system = self.cache_system
        
        # Add cache middleware
        app.add_middleware(CacheMiddleware, cache_system=self.cache_system)
    
    def configure_route_cache(self, path: str, duration: int) -> None:
        """
        Configure caching for a specific route.
        
        Args:
            path: Route path
            duration: Cache duration in seconds
        """
        self.cache_system.configure_route_cache(path, duration)
    
    def get_cache_config(self) -> Dict[str, int]:
        """
        Get the current cache configuration.
        
        Returns:
            Dictionary mapping route paths to cache durations
        """
        return self.cache_system.get_cache_config()
    
    def clear_cache(self, path: Optional[str] = None) -> None:
        """
        Clear cache for a specific route or all routes.
        
        Args:
            path: Route path, or None to clear all caches
        """
        self.cache_system.clear_cache(path)
    
    def prompt_for_caching(self, model_name: str) -> Optional[int]:
        """
        Prompt user for caching configuration for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Cache duration in seconds, or None if caching is not desired
        """
        print(f"\nWould you like to cache the {model_name} model's routes?")
        print("Caching can improve performance but may serve stale data.")
        
        choice = input("Cache routes? (y/n): ").strip().lower()
        
        if choice != 'y':
            return None
        
        print("\nSelect caching period:")
        print("1) 30 seconds")
        print("2) 1 minute")
        print("3) 5 minutes")
        print("4) 15 minutes")
        print("5) 30 minutes")
        print("6) 1 hour")
        print("7) Custom period")
        
        option = input("Select an option (1-7): ").strip()
        
        duration_map = {
            "1": 30,
            "2": 60,
            "3": 300,
            "4": 900,
            "5": 1800,
            "6": 3600,
        }
        
        if option in duration_map:
            return duration_map[option]
        elif option == "7":
            try:
                custom_seconds = int(input("Enter custom cache duration in seconds: "))
                if custom_seconds > 0:
                    return custom_seconds
                else:
                    print("Invalid duration. Using default of 60 seconds.")
                    return 60
            except ValueError:
                print("Invalid input. Using default of 60 seconds.")
                return 60
        else:
            print("Invalid option. Using default of 60 seconds.")
            return 60
    
    def configure_model_caching(self, model_name: str, duration: int) -> None:
        """
        Configure caching for all routes of a model.
        
        Args:
            model_name: Name of the model
            duration: Cache duration in seconds
        """
        # Configure GET routes for the model
        base_path = f"/{model_name.lower()}s"
        
        # Configure list route
        self.configure_route_cache(base_path, duration)
        
        # Configure detail route pattern
        # Note: This is a pattern match, actual implementation would need to be more sophisticated
        self.configure_route_cache(f"{base_path}/{{id}}", duration)
        
        print(f"Configured caching for {model_name} routes with {duration} seconds duration.")
