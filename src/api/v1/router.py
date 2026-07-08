"""API v1 router composition."""

from fastapi import APIRouter

from api.v1 import admin, auth, customer, intelligence, products

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router, tags=["auth"])
router.include_router(products.router, tags=["products"])
router.include_router(customer.router, tags=["customer"])
router.include_router(admin.router, tags=["admin"])
router.include_router(intelligence.router, tags=["intelligence"])
