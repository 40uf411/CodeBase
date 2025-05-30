from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

import core.database

from .base_repository import BaseRepository
from models.invoice import Invoice
from core.database import get_async_db # For dependency injection

class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: AsyncSession):
        super().__init__(Invoice, db)

    # Add any entity-specific repository methods here if needed
    # Example:
    # async def get_by_some_field(self, field_value: str) -> Optional[Invoice]:
    #     query = select(self.model).filter(self.model.some_field == field_value, self.model.is_deleted == False)
    #     result = await self.db.execute(query)
    #     return result.scalars().first()

def get_invoice_repository(db: AsyncSession = Depends(get_async_db)) -> InvoiceRepository:
    return InvoiceRepository(db)