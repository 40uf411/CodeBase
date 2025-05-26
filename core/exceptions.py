# core/exceptions.py
class RepositoryError(Exception):
    """Base class for repository-related errors."""
    pass

class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found in the repository."""
    def __init__(self, entity_name: str, entity_id: any):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with ID '{entity_id}' not found.")

class DuplicateEntityError(RepositoryError):
    """Raised when attempting to create an entity that already exists (e.g., unique constraint)."""
    def __init__(self, entity_name: str, params: dict):
        self.entity_name = entity_name
        self.params = params
        super().__init__(f"{entity_name} with params {params} already exists or violates a unique constraint.")
