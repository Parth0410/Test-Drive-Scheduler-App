from fastapi import APIRouter

from app.api.routes import bookings, dealer, inventory

api_router = APIRouter()
api_router.include_router(inventory.router)
api_router.include_router(bookings.router)
api_router.include_router(dealer.router)


@api_router.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
