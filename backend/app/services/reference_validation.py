from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConfigItem, ServiceContract


def validate_asset_links(
    db: Session,
    *,
    tenant_id: str,
    config_item_id: str | None,
    contract_id: str | None,
) -> None:
    if config_item_id:
        config_item = db.scalar(
            select(ConfigItem.id).where(ConfigItem.id == config_item_id, ConfigItem.tenant_id == tenant_id)
        )
        if config_item is None:
            raise HTTPException(status_code=400, detail="Invalid config item reference")

    if contract_id:
        contract = db.scalar(
            select(ServiceContract.id).where(
                ServiceContract.id == contract_id,
                ServiceContract.tenant_id == tenant_id,
            )
        )
        if contract is None:
            raise HTTPException(status_code=400, detail="Invalid contract reference")
