# Third party imports
from celery import shared_task

# Django imports
from django.core.management import call_command

# Module imports
from plane.utils.exception_logger import log_exception


@shared_task
def sync_vj_reputation_task():
    """
    Recomputes contribution snapshots and reputation scores for every VJ
    Startups member, reusing the same logic as the `sync_contributions`
    management command so the scheduled run and the manual one never drift.
    """
    try:
        call_command("sync_contributions")
    except Exception as e:
        log_exception(e)
