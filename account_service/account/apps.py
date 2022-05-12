from logging import getLogger
from django.apps import AppConfig
from django.conf import settings


logger = getLogger(__name__)


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'

    def ready(self):
        try:
            from account.models import Account
            from account.models import AccountUser
        
            company_user, is_new = AccountUser.objects.get_or_create(username=settings.COMPANY_SLUG, role='admin')
            company_account, is_new = Account.objects.get_or_create(user=company_user)
            if is_new:
                logger.info(f'created company {company_account=}, {company_user=}')
        except Exception as e:
            logger.exception('app not ready')
