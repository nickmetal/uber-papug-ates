from datetime import datetime
import json
from typing import Dict
from pathlib import Path
from uuid import UUID
from jsonschema.validators import Draft202012Validator, Draft4Validator
from jsonschema.validators import extend
from functools import lru_cache


def check_string_formats(checker, instance):
    return (
        Draft202012Validator.TYPE_CHECKER.is_type(instance, "string") or isinstance(instance, UUID) or isinstance(instance, datetime)
    )


@lru_cache
def get_schema(schema_path: str) -> Dict:
    with Path(schema_path) as path:
        return json.loads(path.read_bytes())


class Validator:
    def __init__(self, schema_path: str) -> None:
        self._schema = get_schema(schema_path)
        self._schema_validator = self.get_validator()

    def validate(self, data: Dict):
        self._schema_validator.validate(data)

    def get_validator(self):
        draft_2_class_map = {
            "http://json-schema.org/draft-04/schema#": Draft4Validator,
            "https://json-schema.org/draft/2020-12/schema": Draft202012Validator,
        }
        base_validator = draft_2_class_map[self._schema['$schema']]
        type_checker = base_validator.TYPE_CHECKER.redefine("string", check_string_formats)
        custom_validator = extend(base_validator, type_checker=type_checker)
        return custom_validator(self._schema)
