import logging
from datetime import datetime
from django.utils import timezone
from django.http import HttpRequest, JsonResponse

from django.views.decorators.http import require_http_methods
from analytics.models import Account
from analytics.models import Task

from common_lib.access_control import requires_scope
from django.db.models import Max


logger = logging.getLogger(__name__)


@requires_scope("admin manager")
@require_http_methods(["GET"])
def get_dashboard(request: HttpRequest):
    company_account = Account.objects.get(user__public_id="1")
    papug_accounts_count = Account.objects.filter(amount__lt=0).exclude(public_id=company_account.public_id).count()

    today_min = datetime.combine(timezone.now().date(), datetime.today().time().min)
    today_max = datetime.combine(timezone.now().date(), datetime.today().time().max)

    today_stats = Task.objects.filter(created_at__range=(today_min, today_max), status="completed").aggregate(
        completed_max_task=Max("fee_on_complete")
    )
    today_top_task = today_stats["completed_max_task"] or 0
    top_tasks = {
        "today_top_task": today_top_task,
        "week_top_tasks": "TODO",
        "month_top_tasks": "TODO",
    }
    today_revenue = company_account.amount  # TODO: read transaction log and filter by today date
    debt_papug_amount = papug_accounts_count
    dashboard = {
        "today_revenue": today_revenue,
        "debt_papug_amount": debt_papug_amount,
        "top_tasks": top_tasks,
    }
    return JsonResponse(data=dashboard)
