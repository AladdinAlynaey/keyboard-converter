from bson import ObjectId
from typing import Dict, List, Any, Optional
from configuration.db import get_db

class BaseRepository:
    def __init__(self, collection_name: str):
        self.db = get_db()
        self.collection = self.db[collection_name]

    def _serialize_id(self, item: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if item is None:
            return None
        if "_id" in item:
            item["id"] = str(item["_id"])
            del item["_id"]
        return item

    def _serialize_list(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self._serialize_id(item) for item in items if item is not None]

    def _to_object_id(self, id_str: str) -> ObjectId:
        try:
            return ObjectId(id_str)
        except Exception:
            raise ValueError(f"Invalid ObjectId format: {id_str}")

    def get_by_id(self, id_str: str) -> Optional[Dict[str, Any]]:
        try:
            item = self.collection.find_one({"_id": self._to_object_id(id_str)})
            return self._serialize_id(item)
        except Exception:
            return None

    def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        item = self.collection.find_one(filter_query)
        return self._serialize_id(item)

    def find_many(self, filter_query: Dict[str, Any], sort: Optional[List[tuple]] = None, limit: int = 0, skip: int = 0) -> List[Dict[str, Any]]:
        cursor = self.collection.find(filter_query)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return self._serialize_list(list(cursor))

    def create(self, data: Dict[str, Any]) -> str:
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def update(self, id_str: str, update_data: Dict[str, Any], filter_query: Optional[Dict[str, Any]] = None) -> bool:
        query = {"_id": self._to_object_id(id_str)}
        if filter_query:
            query.update(filter_query)
        
        # Avoid overriding _id
        if "_id" in update_data:
            del update_data["_id"]

        result = self.collection.update_one(query, {"$set": update_data})
        return result.modified_count > 0

    def delete(self, id_str: str, filter_query: Optional[Dict[str, Any]] = None) -> bool:
        query = {"_id": self._to_object_id(id_str)}
        if filter_query:
            query.update(filter_query)
        result = self.collection.delete_one(query)
        return result.deleted_count > 0

    def count(self, filter_query: Dict[str, Any]) -> int:
        return self.collection.count_documents(filter_query)
