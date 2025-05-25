# routers/__init__.py

import pkgutil
import importlib
from fastapi import FastAPI
from core.config import settings

def register_routers(app: FastAPI):
    prefix = settings.PROJECT_VER_STR
    package = importlib.import_module(__name__)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{__name__}.{module_name}")
        if hasattr(module, "router"):
            app.include_router(module.router, prefix=prefix, tags=[module_name])
            
