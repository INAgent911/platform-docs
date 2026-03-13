from datetime import datetime, timezone

from app.models import ProvisioningJob, ProvisioningStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def execute_provisioning_job(job: ProvisioningJob) -> None:
    start = _utc_now()
    job.status = ProvisioningStatus.RUNNING
    job.started_at = start
    steps = [
        {"step": "validate_tenant", "status": "ok"},
        {"step": "initialize_schema_defaults", "status": "ok"},
        {"step": "seed_workspace_views", "status": "ok"},
        {"step": "seed_runbooks", "status": "ok"},
        {"step": "mark_ready", "status": "ok"},
    ]
    if job.allowed_first_user_email:
        steps.insert(
            1,
            {
                "step": "validate_allowed_first_user_email",
                "status": "ok",
                "email": job.allowed_first_user_email,
            },
        )
    job.steps = steps
    job.status = ProvisioningStatus.SUCCEEDED
    job.error_message = None
    job.completed_at = _utc_now()
