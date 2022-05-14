import logging
from typing import Dict
from datetime import datetime
from django.utils import timezone
from django.http import HttpRequest, JsonResponse

from django.views.decorators.http import require_http_methods
# from account.models import Task
# from account.controllers import get_company_user

from common_lib.access_control import requires_scope, get_default_session, get_user_info
# from account.models import Account
from django.db.models import Sum


logger = logging.getLogger(__name__)



@requires_scope("admin manager")
@require_http_methods(["GET"])
def get_dashboard(request: HttpRequest):
    
    # Нужно указывать, сколько заработал топ-менеджмент за сегодня и сколько попугов ушло в минус.
    # Нужно показывать самую дорогую задачу за день, неделю или месяц.
    # a) самой дорогой задачей является задача с наивысшей ценой из списка всех закрытых задач за определенный период времени

    # b) пример того, как это может выглядеть:

    # 03.03 — самая дорогая задача — 28$
    # 02.03 — самая дорогая задача — 38$
    # 01.03 — самая дорогая задача — 23$
    # 01-03 марта — самая дорогая задача — 38$
    dashboard = {
        'today_revenue': today_revenue,
        'debt_papug_amount': debt_papug_amount,
        'top_tasks': top_tasks,
    }
    return JsonResponse(data=dashboard)
