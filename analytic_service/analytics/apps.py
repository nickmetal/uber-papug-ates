from logging import getLogger
from django.apps import AppConfig


logger = getLogger(__name__)


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
