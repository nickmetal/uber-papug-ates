from common_lib.di_container import Container
from . import settings


container = Container()
container.config.from_dict(settings.__dict__)
