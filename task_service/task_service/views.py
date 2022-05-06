import json
from http import HTTPStatus
from django.http import HttpRequest, JsonResponse
# from oauth2_provider.decorators import protected_resource
# from users.models import Employee, EmployeeDTO
# from users.forms import SignUpForm, PatchRoleForm
from django.views.decorators.http import require_http_methods
import logging
from requests_oauthlib import OAuth2Session
from django.conf import settings
from django.shortcuts import redirect
from task_service.access_control import requires_scope

logger = logging.getLogger(__name__)


# class TestApiEndpoint(ScopedProtectedResourceView):
#     required_scopes = ["test"]
#     # required_scopes = ['can_make_it can_break_it']

#     def get(self, request, *args, **kwargs):
#         print(f"{request.user.is_anonymous=}")
#         print(f"{request.user.is_authenticated=}")
#         print(f"{request.user=}")
        
#         # import ipdb

#         # ipdb.set_trace()
#         return JsonResponse(data={"status": "ok"})




# def validate_request(form_model):
#     def decorator(func):
#         def wrapper(request):
#             try:
#                 content = request.POST.dict() or json.loads(request.body)
#                 form = form_model(content)
#             except json.decoder.JSONDecodeError as e:
#                 logger.exception("invalid body payload received")
#                 return JsonResponse(
#                     data={"status": "error", "details": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR
#                 )

#             if form.is_valid():
#                 try:
#                     return func(request, form)
#                 except Exception as e:
#                     logger.exception("decorated controller error")
#                     return JsonResponse(
#                         data={"status": "error", "details": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR
#                     )
#             return JsonResponse(data={"error": form.errors}, status=HTTPStatus.BAD_REQUEST)

#         return wrapper

#     return decorator


# # @validate_request(PatchRoleForm)
# @require_http_methods(["PATCH"])
# # @protected_resource(scopes=["read write"])  # TODO: check it
# def assign_role(request: HttpRequest, form: PatchRoleForm):
#     patch = json.loads(request.body)
#     try:
#         employee = Employee.objects.get(id=patch["id"])
#     except Employee.DoesNotExist:
#         return JsonResponse(data={"status": "error", "details": "not_exists"}, status=HTTPStatus.NOT_FOUND)

#     employee.role = patch["role"]
#     employee.save()
#     employee_dto = EmployeeDTO(
#         id=employee.id,
#         name=employee.username,
#         created_at=employee.created_at,
#         updated_at=employee.updated_at,
#         role=employee.role,
#         email=employee.email,
#     )
#     return JsonResponse(data={"status": "ok", "employee": employee_dto.to_dict()})


@requires_scope("admin manager worker")
@require_http_methods(["GET"])
def get_task(request: HttpRequest):
    return JsonResponse(data={"status": "ok"})

@requires_scope("admin manager worker")
@require_http_methods(["GET"])
def add_task(request: HttpRequest):
    return JsonResponse(data={"status": "ok"})
