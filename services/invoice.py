from uuid import UUID
from typing import List, Optional # Added List and Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Request # Added Request

from core.database import get_async_db
from core.exceptions import EntityNotFoundError, DuplicateEntityError # Add other custom exceptions
from models.invoice import Invoice
from schemas.invoice_schema import InvoiceCreate, InvoiceUpdate
from repositories.invoice_repository import InvoiceRepository
# Import other repositories if needed for relationships

class InvoiceService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.repository = InvoiceRepository(db_session)
        # Initialize other repositories here if needed
        # self.privilege_service = PrivilegeService(db_session) # If managing privileges here

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        return await self.repository.get_all(skip=skip, limit=limit)

    async def get_by_id(self, item_id: UUID) -> Optional[Invoice]:
        return await self.repository.get(item_id)

    async def create(self, item_in: InvoiceCreate, request: Optional[Request] = None) -> Invoice:
        # Potentially check for duplicate entries based on unique fields

        # existing_item = await self.repository.get_by_field(item_in.unique_field)
        # if existing_item:
        #     raise DuplicateEntityError(entity_name="Invoice", conflicting_field="unique_field")

        # Create privileges for the new entity type if not exists (usually done once)
        # await self.privilege_service.create_crud_privileges("invoice")

        new_item = await self.repository.create(item_in.dict())
        # Add any post-creation logic here (e.g., logging, notifications)
        return new_item

    async def update(self, item_id: UUID, item_in: InvoiceUpdate, request: Optional[Request] = None) -> Optional[Invoice]:
        existing_item = await self.repository.get(item_id)
        if not existing_item:
            return None # Or raise EntityNotFoundError

        updated_item = await self.repository.update(item_id, item_in.dict(exclude_unset=True))
        # Add any post-update logic here
        return updated_item

    async def delete(self, item_id: UUID, hard_delete: bool = False, request: Optional[Request] = None) -> Optional[Invoice]:
        existing_item = await self.repository.get(item_id)
        if not existing_item:
            return None # Or raise EntityNotFoundError

        deleted_item = await self.repository.delete(item_id, hard_delete=hard_delete)
        # Add any post-deletion logic here
        return deleted_item

    # Add methods for handling relationships if complex logic is needed
    # e.g., async def add_related_entity_to_invoice(...)

def get_invoice_service(db_session: AsyncSession = Depends(get_async_db)) -> InvoiceService:
    return InvoiceService(db_session)