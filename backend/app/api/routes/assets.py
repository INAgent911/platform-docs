from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_any_permission, require_permission
from app.models import ConfigItem, ServiceContract, User
from app.schemas import (
    ConfigItemCreate,
    ConfigItemOut,
    ServiceContractCreate,
    ServiceContractOut,
)
from app.services.audit import log_audit_event
from app.services.usage import log_usage_event

router = APIRouter()


@router.get("/config-items", response_model=list[ConfigItemOut])
def list_config_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("asset.read", "asset.manage")),
) -> list[ConfigItemOut]:
    query = select(ConfigItem).where(ConfigItem.tenant_id == current_user.tenant_id).order_by(ConfigItem.created_at.desc())
    return list(db.scalars(query))


@router.post("/config-items", response_model=ConfigItemOut, status_code=status.HTTP_201_CREATED)
def create_config_item(
    payload: ConfigItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("asset.manage")),
) -> ConfigItemOut:
    item = ConfigItem(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        item_type=payload.item_type,
        environment=payload.environment,
        criticality=payload.criticality,
    )
    db.add(item)
    db.flush()
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="asset.config_item.create",
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="asset.config_item_create",
        resource_type="config_item",
        resource_id=item.id,
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("/contracts", response_model=list[ServiceContractOut])
def list_service_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("asset.read", "asset.manage")),
) -> list[ServiceContractOut]:
    query = (
        select(ServiceContract)
        .where(ServiceContract.tenant_id == current_user.tenant_id)
        .order_by(ServiceContract.created_at.desc())
    )
    return list(db.scalars(query))


@router.post("/contracts", response_model=ServiceContractOut, status_code=status.HTTP_201_CREATED)
def create_service_contract(
    payload: ServiceContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("asset.manage")),
) -> ServiceContractOut:
    contract = ServiceContract(
        tenant_id=current_user.tenant_id,
        contract_code=payload.contract_code,
        customer_name=payload.customer_name,
        sla_tier=payload.sla_tier,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )
    db.add(contract)
    db.flush()
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="asset.contract.create",
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="asset.contract_create",
        resource_type="service_contract",
        resource_id=contract.id,
    )
    db.commit()
    db.refresh(contract)
    return contract
