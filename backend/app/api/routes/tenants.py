from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import Tenant, User
from app.schemas import TenantOut

router = APIRouter()


@router.get("/me", response_model=TenantOut)
def get_my_tenant(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> TenantOut:
    tenant = db.scalar(select(Tenant).where(Tenant.id == current_user.tenant_id))
    return tenant

