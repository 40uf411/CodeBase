from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Path, Query, Response, Request

from core.auth import require_privileges
core.cache.system import cache_response # Assuming caching might be desired
from services.invoice_service import InvoiceService, get_invoice_service
from schemas.invoice_schema import InvoiceResponse, InvoiceCreate, InvoiceUpdate
from utils.activity_logging_decorators import log_activity # If activity logging is used

router = APIRouter(
    prefix="/invoices", # Pluralized entity name
    tags=["invoice"],
    dependencies=[require_privileges("invoice:read")] # Basic read privilege
)

@router.get("/", response_model=List[InvoiceResponse], summary="List Invoices")
@cache_response(ttl=3600) # Example: Cache for 1 hour
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: InvoiceService = Depends(get_invoice_service)
) -> List[InvoiceResponse]:
    items = await service.get_all(skip=skip, limit=limit)
    return items

@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[require_privileges("invoice:create")],
             summary="Create a new Invoice")
@log_activity(success_event_type="INVOICE_CREATE_SUCCESS", failure_event_type="INVOICE_CREATE_FAILURE")
async def create_invoice(
    item_in: InvoiceCreate,
    request: Request, # For log_activity
    service: InvoiceService = Depends(get_invoice_service)
) -> InvoiceResponse:
    # Note: privilege creation (service.create_crud_privileges) should be handled elsewhere or once
    return await service.create(item_in, request=request) # Assuming create method in service

@router.get("/{item_id}", response_model=InvoiceResponse, summary="Get a Invoice by ID")
@cache_response(ttl=3600)
async def get_invoice(
    item_id: UUID = Path(..., title="Invoice ID"),
    service: InvoiceService = Depends(get_invoice_service)
) -> InvoiceResponse:
    item = await service.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return item

@router.put("/{item_id}", response_model=InvoiceResponse,
             dependencies=[require_privileges("invoice:update")],
             summary="Update a Invoice")
@log_activity(success_event_type="INVOICE_UPDATE_SUCCESS", failure_event_type="INVOICE_UPDATE_FAILURE")
async def update_invoice(
    item_in: InvoiceUpdate,
    request: Request, # For log_activity
    item_id: UUID = Path(..., title="Invoice ID"),
    service: InvoiceService = Depends(get_invoice_service)
) -> InvoiceResponse:
    updated_item = await service.update(item_id, item_in, request=request) # Assuming update method
    if not updated_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found for update")
    return updated_item

@router.delete("/{item_id}", response_model=InvoiceResponse,
               dependencies=[require_privileges("invoice:delete")],
               summary="Delete a Invoice")
@log_activity(success_event_type="INVOICE_DELETE_SUCCESS", failure_event_type="INVOICE_DELETE_FAILURE")
async def delete_invoice(
    request: Request, # For log_activity
    item_id: UUID = Path(..., title="Invoice ID"),
    hard_delete: bool = Query(False, description="Permanently delete if true"),
    service: InvoiceService = Depends(get_invoice_service)
) -> InvoiceResponse:
    deleted_item = await service.delete(item_id, hard_delete=hard_delete, request=request) # Assuming delete
    if not deleted_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found for deletion")
    return deleted_item