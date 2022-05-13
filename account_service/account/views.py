import json
import random
import logging
from typing import Dict

from django.http import HttpRequest, JsonResponse

from django.views.decorators.http import require_http_methods

from account_service.access_control import requires_scope, get_default_session, get_user_info
from account.models import Account
from common_lib.cud_event_manager import EventManager
from common_lib.rabbit import RabbitMQPublisher
from account.models import AccountUser


logger = logging.getLogger(__name__)


# TODO: instead of global clients do: add DI IoC:
# https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html
# event_manager = EventManager(RabbitMQPublisher())


def get_worker_dashboard(request) -> Dict:
    logger.debug("getting worker dashboard")
    dashboard = {}
    return dashboard


def get_admin_dashboard(request) -> Dict:
    logger.debug("getting admin dashboard")
    dashboard = {}
    return dashboard


@requires_scope("admin manager worker")
@require_http_methods(["GET"])
def get_dashboard(request: HttpRequest):
    session = get_default_session(token_info={"access_token": request.session["access_token"], "token_type": "Bearer"})
    match get_user_info(session)["role"]:
        case "worker":
            info = get_worker_dashboard(request)
        case "admin" | "manager":
            info = get_admin_dashboard(request)
        case _:
            raise ValueError("Unknown role")

    return JsonResponse(data=info)
