from repositories.base import BaseRepository
from bson import ObjectId
from typing import Dict, List, Any, Optional
import datetime

class HistoryRepository(BaseRepository):
    def __init__(self):
        super().__init__("history")

    def log_conversion(self, user_id: str, original_text: str, converted_text: str, 
                       layout_id: str, layout_name: str, mode: int, 
                       ai_enhanced_text: Optional[str] = None) -> str:
        history_item = {
            "user_id": user_id,
            "original_text": original_text,
            "converted_text": converted_text,
            "ai_enhanced_text": ai_enhanced_text,
            "layout_id": layout_id,
            "layout_name": layout_name,
            "mode": mode,
            "timestamp": datetime.datetime.utcnow()
        }
        return self.create(history_item)

    def get_user_history(self, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
        return self._serialize_list(list(cursor))

    def delete_history_item(self, history_id: str, user_id: str) -> bool:
        return self.delete(history_id, filter_query={"user_id": user_id})

    def clear_user_history(self, user_id: str) -> bool:
        result = self.collection.delete_many({"user_id": user_id})
        return result.deleted_count > 0

    def get_conversion_statistics(self, user_id: str) -> Dict[str, Any]:
        # Aggregate statistics
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_conversions": {"$sum": 1},
                "total_chars_converted": {"$sum": {"$strLenCP": "$original_text"}},
                "modes_used": {"$push": "$mode"}
            }}
        ]
        results = list(self.collection.aggregate(pipeline))
        if not results:
            return {
                "total_conversions": 0,
                "total_chars_converted": 0,
                "mode_counts": {1: 0, 2: 0, 3: 0, 4: 0}
            }
        
        stat = results[0]
        modes_used = stat.get("modes_used", [])
        mode_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for m in modes_used:
            if m in mode_counts:
                mode_counts[m] += 1

        return {
            "total_conversions": stat.get("total_conversions", 0),
            "total_chars_converted": stat.get("total_chars_converted", 0),
            "mode_counts": mode_counts
        }
