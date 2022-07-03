from logging import getLogger
from django.apps import AppConfig
from django.conf import settings

from common_lib.cud_event_manager import CUDEvent, EventManager, FailedEventManager, ServiceName
from common_lib.rabbit import RabbitMQPublisher
from account_service import container


logger = getLogger(__name__)


class AccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "account"

    def ready(self):
        container.wire(modules=[".views", f"{self.name}.management.commands.consume_cud_events"])

        try:
            from account.models import Account
            from account.models import AccountUser

            company_user, is_new = AccountUser.objects.get_or_create(
                username=settings.COMPANY_SLUG, role="admin", public_id="1"
            )
            # TODO: add uniq const
            company_account, is_new = Account.objects.get_or_create(user=company_user)
            if is_new:
                failed_event_manager = FailedEventManager.build(
                    mongo_dsn=settings.MONGO_DSN,
                    db_name=settings.MONGO_DB_NAME,
                    error_collection_name=settings.MONGO_ERROR_COLLECTION,
                )
                event_manager = EventManager(
                    mq_publisher=RabbitMQPublisher(
                        exchange_name=settings.BILLING_EXCHANGE_NAME, dsn=settings.RABBITMQ_DSN
                    ),
                    schema_basedir=settings.EVENT_SCHEMA_DIR,
                    service_name=ServiceName.ACCOUNT_SERVICE,
                    failed_event_manager=failed_event_manager,
                    offset_manager=None,
                )
                logger.info(f"created company {company_account=}, {company_user=}")
                event_manager.send_event(
                    CUDEvent(
                        data={
                            "account_public_id": company_account.public_id,
                            "user_public_id": company_user.public_id,
                            "role": company_user.role,
                        },
                        producer="account_service",
                        event_name="billing_account_created",
                    )
                )
        except Exception:
            logger.warning("app not ready")
