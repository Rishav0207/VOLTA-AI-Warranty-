"""Product catalog routes."""

from fastapi import APIRouter, Depends, Query

import schemas
from repositories.product_repository import get_product_with_warranty, list_products
from security.auth import get_current_user

router = APIRouter()


@router.get("/products", response_model=list[schemas.ProductOut])
async def products(
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = "name",
    user: dict = Depends(get_current_user),
) -> list[schemas.ProductOut]:
    """List catalog products with filtering, sorting, and pagination."""
    return [schemas.ProductOut(**row) for row in list_products(search=search, limit=limit, offset=offset, sort=sort)]


@router.get("/products/{product_id}", response_model=schemas.ProductDetailOut)
async def product_detail(product_id: int, user: dict = Depends(get_current_user)) -> schemas.ProductDetailOut:
    """Return a catalog product and its warranty metadata."""
    row = get_product_with_warranty(product_id)
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Product not found.")
    return schemas.ProductDetailOut(**row)
