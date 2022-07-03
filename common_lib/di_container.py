from dependency_injector import containers, providers
from pymongo.mongo_client import MongoClient

from common_lib.rabbit import RabbitMQPublisher
from common_lib.offset_manager import OffsetLogManager
from common_lib.cud_event_manager import FailedEventManager, EventManager


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    rabbit_publisher = providers.Singleton(
        RabbitMQPublisher, exchange_name=config.TASKS_EXCHANGE_NAME, dsn=config.RABBITMQ_DSN
    )
    mongo_client = providers.Singleton(MongoClient, config.MONGO_DSN)
    failed_event_manager = providers.Singleton(
        FailedEventManager.build,
        mongo_client=mongo_client,
        db_name=config.MONGO_DB_NAME,
        error_collection_name=config.MONGO_ERROR_COLLECTION,
    )
    offset_manager = providers.Singleton(
        OffsetLogManager.build,
        mongo_client=mongo_client,
        db_name=config.MONGO_DB_NAME,
        collection_name=config.OFFSET_COLLECTION,
    )
    event_manager = providers.Singleton(
        EventManager,
        mq_publisher=rabbit_publisher,
        schema_basedir=config.EVENT_SCHEMA_DIR,
        service_name=config.SERVICE_NAME,
        failed_event_manager=failed_event_manager,
        offset_manager=offset_manager,
    )
