import logging
from typing import Dict
from datetime import datetime
from django.utils import timezone
from django.http import HttpRequest, JsonResponse

from django.views.decorators.http import require_http_methods
from account.models import Task
from account.controllers import get_company_user

from common_lib.access_control import requires_scope, get_default_session, get_user_info
from account.models import Account
from django.db.models import Sum


logger = logging.getLogger(__name__)


def get_worker_dashboard(request, user: Dict) -> Dict:
    """Provides current account and audit log messages"""
    logger.debug(f"getting worker dashboard, {user=}")
    account = Account.objects.get(user__public_id=user["public_id"])

    today_min = datetime.combine(timezone.now().date(), datetime.today().time().min)
    today_max = datetime.combine(timezone.now().date(), datetime.today().time().max)
    queryset = account.source_account.filter(created_at__range=(today_min, today_max)).order_by("created_at")

    log_records = []
    for trx in queryset:
        log_records.append({"description": trx.description, "amount": trx.amount, "created_at": trx.created_at})

    dashboard = {"today_revenue": account.amount, "log_records": log_records}
    return dashboard


def get_admin_dashboard(request, user: Dict) -> Dict:
    """Provides daily stats and audit log messages"""
    logger.debug(f"getting admin dashboard, {user=}")
    today_min = datetime.combine(timezone.now().date(), datetime.today().time().min)
    today_max = datetime.combine(timezone.now().date(), datetime.today().time().max)

    # get today's company account stats
    # TODO: aggregate per each day
    stats = (
        Task.objects.filter(created_at__range=(today_min, today_max))
        .order_by("created_at")
        .aggregate(assigned_sum=Sum("fee_on_assign"), completed_sum=Sum("fee_on_complete"))
    )

    assigned_sum = stats["assigned_sum"] or 0
    completed_sum = stats["completed_sum"] or 0

    today_revenue = (assigned_sum + completed_sum) * -1

    # get log records for today
    company_user = get_company_user()
    account = Account.objects.get(user=company_user)
    queryset = account.target_account.filter(created_at__range=(today_min, today_max)).order_by("created_at")

    log_records = []
    for trx in queryset:
        log_records.append({"description": trx.description, "amount": -trx.amount, "created_at": trx.created_at})

    dashboard = {
        "today_revenue": today_revenue,
        "log_records": log_records,
    }
    return dashboard


@requires_scope("admin manager worker")
@require_http_methods(["GET"])
def get_dashboard(request: HttpRequest):
    session = get_default_session(token_info={"access_token": request.session["access_token"], "token_type": "Bearer"})
    user = get_user_info(session)
    match user["role"]:
        case "worker":
            info = get_worker_dashboard(request, user)
        case "admin" | "manager":
            info = get_admin_dashboard(request, user)
        case _:
            raise ValueError("Unknown role")

    return JsonResponse(data=info)
