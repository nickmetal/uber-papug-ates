import json
import random
import logging
from typing import Dict
from dataclasses import asdict
from django.http import HttpRequest, JsonResponse

from django.views.decorators.http import require_http_methods
from django.db import transaction

from task_service.access_control import requires_scope
from task.models import Task, TaskDTO, TaskStatus
from task.cud_event_manager import EventManager, TaskCreatedEvent
from task.rabbit import RabbitMQClient

logger = logging.getLogger(__name__)

#TODO: instead of global clients do: add DI IoC:
# https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html
event_manager = EventManager(mq_client=RabbitMQClient())


def serialize_task(task: Task) -> Dict:
    dto = TaskDTO(
        id=task.id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        title=task.title,
        description=task.description,
        status=task.status,
        assignee=task.assignee,
        fee_on_assign=task.fee_on_assign,
        fee_on_complete=task.fee_on_complete,
    )
    return asdict(dto)


@requires_scope("admin manager worker")
@require_http_methods(["GET"])
def get_task(request: HttpRequest, task_id: int):
    task = Task.objects.get(id=task_id)
    return JsonResponse(data=serialize_task(task))


@requires_scope("admin manager worker")
@require_http_methods(["POST"])
def add_task(request: HttpRequest):
    body = json.loads(request.body)
    body['fee_on_assign'] = round(random.uniform(-10, -20), 2)
    body['fee_on_complete'] = round(random.uniform(20, 40), 2)
    
    # TODO: check that user not manager/admin
    # assignee = body['assignee']
    # TODO: add form validation
    task = Task.objects.create(**body)
    data = serialize_task(task)
    event = TaskCreatedEvent(data=data)
    event_manager.send_event(event=event)
    return JsonResponse(data=data)

@requires_scope("admin manager worker")
@require_http_methods(["PUT"])
def update_task(request: HttpRequest):
    body = json.loads(request.body)
    id_ = body['id']
    Task.objects.filter(id=id_).update(**body)
    return JsonResponse(data={"status": "updated"})


# @requires_scope("admin manager")
@require_http_methods(["POST"])
def shuffle_tasks(request: HttpRequest):
    """Randomly shuffles not completed tasks across all users.
    
    Note: probably has distribution transaction issue, need to redesign and fix that 
    """
    queryset = Task.objects.select_for_update().filter(status=TaskStatus.NEW.value)
    
    #TODO: obtain account ids from account service
    # TODO: send events to bus about that shuffle
    users = [1,2,3]
    with transaction.atomic():
        tasks = []
        for task in queryset:
        
            user_id = random.choice(users)    
            previous_user_id = task.assignee
            task.assignee = user_id
            task.save()
            
            
            tasks.append(task)   
            logger.debug(f'new {task.assignee=} in {task=} due to shuffle operation. previous {previous_user_id}')
            
    return JsonResponse(data={"status": "shuffled", "tasks": len(tasks)})
