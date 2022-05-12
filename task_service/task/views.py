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
from task.cud_event_manager import EventManager, TaskCreatedEvent, TasksAssignedEvent, TaskCompletedEvent
from task.rabbit import RabbitMQClient
from task.models import TaskTrackerUser


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
        assignee=task.assignee.public_id,
        fee_on_assign=task.fee_on_assign,
        fee_on_complete=task.fee_on_complete,
        jira_id=task.jira_id,
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
    # TODO: add form validation
    body = json.loads(request.body)
    body['fee_on_assign'] = round(random.uniform(-10, -20), 2)
    body['fee_on_complete'] = round(random.uniform(20, 40), 2)
    body['assignee'] = TaskTrackerUser.objects.get(public_id=body['assignee'])
    
    # TODO: check that user not manager/admin
    task = Task.objects.create(**body)
    response_data = serialize_task(task)
    event_manager.send_event(event=TaskCreatedEvent(data=response_data))
    return JsonResponse(data=response_data)

@requires_scope("admin manager worker")
@require_http_methods(["PUT"])
def update_task(request: HttpRequest):
    """Is used by seeting complete status"""
    body = json.loads(request.body)
    id_ = body['id']
    Task.objects.filter(id=id_).update(**body)
    if body['status'] == 'completed':
        data = {'id': id_, 'status': 'completed'}
        event_manager.send_event(event=TaskCompletedEvent(data=data))
    return JsonResponse(data={"status": "updated"})


@requires_scope("admin manager")
@require_http_methods(["POST"])
def shuffle_tasks(request: HttpRequest):
    """Randomly shuffles not completed tasks across all users.
    
    Note: probably has distribution transaction issue, need to redesign and fix that 
    """

    tasks = []
    # TODO: think how to do random choise not in all-in-memory
    with transaction.atomic():
        task_queryset = Task.objects.select_for_update().filter(status=TaskStatus.NEW.value)
        users = list(TaskTrackerUser.objects.filter(role='worker'))
        for task in task_queryset:
        
            task_user = random.choice(users)    
            previous_user_id = task.assignee.public_id
            task.assignee = task_user
            task.save()
            
            task_item = {
                "id": task.id,
                "new_assignee": task_user.public_id,
                "previous_assignee": previous_user_id,
                "fee_on_assign": task.fee_on_assign,
                "fee_on_complete": task.fee_on_complete,
            }
            tasks.append(task_item)  
            logger.debug(f'new {task.assignee=} in {task=} due to shuffle operation. previous {previous_user_id}')

    event = TasksAssignedEvent(data={"tasks": tasks})
    event_manager.send_event(event=event)
            
    return JsonResponse(data={"status": "shuffled", "tasks": tasks})
