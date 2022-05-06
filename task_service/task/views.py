import json
from http import HTTPStatus
from typing import Dict
from django.http import HttpRequest, JsonResponse

from django.views.decorators.http import require_http_methods
import logging
from task_service.access_control import requires_scope
from task.models import DTOJSONEncoder, Task, TaskDTO

logger = logging.getLogger(__name__)


def serialize_task(task: Task) -> Dict:
    return  TaskDTO(
        id=task.id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        title=task.title,
        description=task.description,
        status=task.status,
        assignee=task.assignee,
    )


@requires_scope("admin manager worker")
# @requires_scope("admin")
@require_http_methods(["GET"])
def get_task(request: HttpRequest, task_id: int):
    task = Task.objects.get(id=task_id)
    return JsonResponse(data=task, encoder=DTOJSONEncoder)


@requires_scope("admin manager worker")
@require_http_methods(["POST"])
def add_task(request: HttpRequest):
    task = Task.objects.create(**request.POST.dict())
    return JsonResponse(data=task, encoder=DTOJSONEncoder)
