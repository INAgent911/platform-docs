from fastapi import APIRouter

from app.api.routes import auth, changes, customers, events, incidents, rbac, schema_controller, tenants, tickets

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(rbac.router, prefix="/rbac", tags=["rbac"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(changes.router, prefix="/changes", tags=["changes"])
api_router.include_router(schema_controller.router, prefix="/schema", tags=["schema"])
