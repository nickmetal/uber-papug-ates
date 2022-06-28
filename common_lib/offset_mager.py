from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional
from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient


@dataclass
class Offset:
    message_id: str
    created_at: datetime


class OffsetLogManager:
    """
    Handles distributed log offset

    Responisble for storing current offset and recovering from last known one.
    """

    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._record_id = 1  # single counter value

    @classmethod
    def build(
        cls,
        mongo_dsn: str,
        db_name: str,
        collection_name: str,
    ) -> "OffsetLogManager":
        collection = MongoClient(mongo_dsn)[db_name][collection_name]
        return cls(collection=collection)

    def set_offset(self, offset: Offset):
        """Stores current offset in db"""
        doc = {**asdict(offset), "_id": self._record_id}
        self._collection.insert_one(doc)

    def get_offet(self) -> Optional[Offset]:
        """Gets current offset from db"""
        doc = self._collection.find_one({"_id": self._record_id}, projection={"_id": 0})
        if doc:
            return Offset(**doc)
