from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_permission
from app.models import ProvisioningJob, ProvisioningStatus, User
from app.schemas import ProvisioningJobCreate, ProvisioningJobOut, ProvisioningJobRetry
from app.services.audit import log_audit_event
from app.services.provisioning import execute_provisioning_job
from app.services.usage import log_usage_event

router = APIRouter()


@router.get("", response_model=list[ProvisioningJobOut])
def list_provisioning_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("provisioning.manage")),
) -> list[ProvisioningJobOut]:
    query = (
        select(ProvisioningJob)
        .where(ProvisioningJob.tenant_id == current_user.tenant_id)
        .order_by(ProvisioningJob.created_at.desc())
    )
    return list(db.scalars(query))


@router.post("", response_model=ProvisioningJobOut, status_code=status.HTTP_201_CREATED)
def create_provisioning_job(
    payload: ProvisioningJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("provisioning.manage")),
) -> ProvisioningJobOut:
    job = ProvisioningJob(
        tenant_id=current_user.tenant_id,
        requested_by_user_id=current_user.id,
        package_name=payload.package_name,
        allowed_first_user_email=payload.allowed_first_user_email,
        status=ProvisioningStatus.QUEUED,
        steps=[],
    )
    db.add(job)
    db.flush()

    execute_provisioning_job(job)
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="provisioning.job",
        units=1,
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="provisioning.execute",
        resource_type="provisioning_job",
        resource_id=job.id,
        event_data={"package_name": job.package_name, "status": job.status.value},
    )
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/retry", response_model=ProvisioningJobOut)
def retry_provisioning_job(
    job_id: str,
    payload: ProvisioningJobRetry,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("provisioning.manage")),
) -> ProvisioningJobOut:
    job = db.scalar(
        select(ProvisioningJob).where(
            ProvisioningJob.id == job_id,
            ProvisioningJob.tenant_id == current_user.tenant_id,
        )
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Provisioning job not found")

    if job.status == ProvisioningStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Provisioning job is already running")

    job.status = ProvisioningStatus.QUEUED
    if payload.reset_error:
        job.error_message = None
    execute_provisioning_job(job)
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="provisioning.retry",
        units=1,
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="provisioning.retry",
        resource_type="provisioning_job",
        resource_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job
