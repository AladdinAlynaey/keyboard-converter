from repositories.base import BaseRepository
from bson import ObjectId
from typing import Dict, List, Any, Optional
import datetime

class LayoutRepository(BaseRepository):
    def __init__(self):
        super().__init__("layouts")
        self.published_collection = self.db["published_layouts"]
        self.favorites_collection = self.db["favorites"]
        self.comments_collection = self.db["comments"]
        self.ratings_collection = self.db["ratings"]

    # --- Core User Layouts CRUD ---
    
    def get_user_layout(self, layout_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            item = self.collection.find_one({"_id": self._to_object_id(layout_id), "user_id": user_id})
            return self._serialize_id(item)
        except Exception:
            return None

    def get_user_layouts(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort("name", 1)
        return self._serialize_list(list(cursor))

    def create_layout(self, user_id: str, data: Dict[str, Any]) -> str:
        data["user_id"] = user_id
        data["is_public"] = data.get("is_public", False)
        data["created_at"] = datetime.datetime.utcnow()
        data["updated_at"] = datetime.datetime.utcnow()
        data["version"] = 1
        return self.create(data)

    def update_layout(self, layout_id: str, user_id: str, update_data: Dict[str, Any]) -> bool:
        update_data["updated_at"] = datetime.datetime.utcnow()
        # Increment version when mapping changes
        if "mapping" in update_data:
            # We can use pymongo direct query for $inc
            self.collection.update_one(
                {"_id": self._to_object_id(layout_id), "user_id": user_id},
                {"$inc": {"version": 1}}
            )
        return self.update(layout_id, update_data, filter_query={"user_id": user_id})

    def delete_layout(self, layout_id: str, user_id: str) -> bool:
        # Delete references too
        try:
            obj_id = self._to_object_id(layout_id)
            self.collection.delete_one({"_id": obj_id, "user_id": user_id})
            self.published_collection.delete_one({"layout_id": layout_id})
            self.favorites_collection.delete_many({"layout_id": layout_id})
            self.comments_collection.delete_many({"layout_id": layout_id})
            self.ratings_collection.delete_many({"layout_id": layout_id})
            return True
        except Exception:
            return False

    def duplicate_layout(self, layout_id: str, user_id: str, new_name: str) -> Optional[str]:
        layout = self.get_user_layout(layout_id, user_id)
        if not layout:
            return None
        
        # Strip ID and set new name
        layout["name"] = new_name
        layout["is_public"] = False
        del layout["id"]
        return self.create_layout(user_id, layout)

    # --- Marketplace Operations ---

    def publish_layout(self, layout_id: str, user_id: str, tags: List[str] = None) -> bool:
        layout = self.get_user_layout(layout_id, user_id)
        if not layout:
            return False

        # Mark main layout as public
        self.update_layout(layout_id, user_id, {"is_public": True})

        # Get user's current name from users collection
        user_doc = self.db["users"].find_one({"_id": self._to_object_id(user_id)})
        creator_name = user_doc.get("name") if user_doc else layout.get("creator_name", "Anonymous")

        # Insert or update snapshot in published_layouts
        published_data = {
            "layout_id": layout_id,
            "user_id": user_id,
            "creator_name": creator_name,
            "name": layout["name"],
            "description": layout.get("description", ""),
            "language": layout["language"],
            "mapping": layout["mapping"],
            "direction": layout.get("direction", "ltr"),
            "version": layout.get("version", 1),
            "tags": tags or [],
            "downloads": 0,
            "likes": 0,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }

        # Check if already published
        existing = self.published_collection.find_one({"layout_id": layout_id})
        if existing:
            # Preserve download and like count, updates name, description, mapping, tags
            published_data["downloads"] = existing.get("downloads", 0)
            published_data["likes"] = existing.get("likes", 0)
            self.published_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": published_data}
            )
        else:
            self.published_collection.insert_one(published_data)
        return True

    def unpublish_layout(self, layout_id: str, user_id: str) -> bool:
        self.update_layout(layout_id, user_id, {"is_public": False})
        result = self.published_collection.delete_one({"layout_id": layout_id, "user_id": user_id})
        return result.deleted_count > 0

    def search_marketplace(self, query: str = "", language: str = "", sort_by: str = "likes", limit: int = 12, skip: int = 0) -> List[Dict[str, Any]]:
        filter_query = {}
        
        # Text search if query provided
        if query:
            filter_query["$text"] = {"$search": query}
        
        if language:
            filter_query["language"] = {"$regex": f"^{language}$", "$options": "i"}

        cursor = self.published_collection.find(filter_query)

        # Sorting strategy
        sort_opts = []
        if sort_by == "downloads":
            sort_opts.append(("downloads", -1))
        elif sort_by == "likes":
            sort_opts.append(("likes", -1))
        elif sort_by == "newest":
            sort_opts.append(("created_at", -1))
        else:
            sort_opts.append(("likes", -1))

        cursor = cursor.sort(sort_opts).skip(skip).limit(limit)
        
        items = list(cursor)
        user_ids = [item["user_id"] for item in items if item.get("user_id")]
        
        # Batch lookup publisher names from the users collection
        user_name_map = {}
        if user_ids:
            try:
                obj_ids = []
                for uid in user_ids:
                    try:
                        obj_ids.append(ObjectId(uid))
                    except Exception:
                        pass
                users = self.db["users"].find({"_id": {"$in": obj_ids}})
                user_name_map = {str(u["_id"]): u.get("name", "Anonymous") for u in users}
            except Exception:
                pass

        results = []
        for item in items:
            # Map _id to id
            item["id"] = str(item["_id"])
            del item["_id"]
            
            # Dynamically attach current publisher name
            item["creator_name"] = user_name_map.get(item.get("user_id"), item.get("creator_name", "Anonymous"))
            
            # Fetch average rating
            rating_stats = self.get_layout_rating_stats(item["layout_id"])
            item["average_rating"] = rating_stats["average"]
            item["ratings_count"] = rating_stats["count"]
            results.append(item)
            
        return results

    def increment_downloads(self, layout_id: str) -> None:
        self.published_collection.update_one(
            {"layout_id": layout_id},
            {"$inc": {"downloads": 1}}
        )

    # --- Favorites Operations ---

    def toggle_favorite(self, user_id: str, layout_id: str) -> Dict[str, Any]:
        # Check if exists
        fav = self.favorites_collection.find_one({"user_id": user_id, "layout_id": layout_id})
        if fav:
            self.favorites_collection.delete_one({"_id": fav["_id"]})
            # Decrement likes in published layout
            self.published_collection.update_one(
                {"layout_id": layout_id},
                {"$inc": {"likes": -1}}
            )
            return {"status": "removed"}
        else:
            self.favorites_collection.insert_one({
                "user_id": user_id,
                "layout_id": layout_id,
                "created_at": datetime.datetime.utcnow()
            })
            # Increment likes in published layout
            self.published_collection.update_one(
                {"layout_id": layout_id},
                {"$inc": {"likes": 1}}
            )
            return {"status": "added"}

    def is_favorite(self, user_id: str, layout_id: str) -> bool:
        return self.favorites_collection.find_one({"user_id": user_id, "layout_id": layout_id}) is not None

    def get_user_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.favorites_collection.find({"user_id": user_id})
        layout_ids = [item["layout_id"] for item in cursor]
        
        # Load details of these layouts from published_layouts or layouts
        # Match layouts from layouts (private but own) or published_layouts (public, potentially owned by others)
        results = []
        for lid in layout_ids:
            try:
                # check published first
                layout = self.published_collection.find_one({"layout_id": lid})
                if layout:
                    layout["id"] = str(layout["_id"])
                    del layout["_id"]
                    results.append(layout)
                else:
                    # check if private own
                    layout = self.collection.find_one({"_id": self._to_object_id(lid)})
                    if layout:
                        layout["id"] = str(layout["_id"])
                        del layout["_id"]
                        layout["layout_id"] = layout["id"] # format consistency
                        results.append(layout)
            except Exception:
                continue

        # Batch lookup publisher names for favorites
        user_ids = [layout.get("user_id") for layout in results if layout.get("user_id")]
        user_name_map = {}
        if user_ids:
            try:
                obj_ids = []
                for uid in user_ids:
                    try:
                        obj_ids.append(ObjectId(uid))
                    except Exception:
                        pass
                users = self.db["users"].find({"_id": {"$in": obj_ids}})
                user_name_map = {str(u["_id"]): u.get("name", "Anonymous") for u in users}
            except Exception:
                pass
                
        for layout in results:
            layout["creator_name"] = user_name_map.get(layout.get("user_id"), layout.get("creator_name", "Anonymous"))

        return results

    # --- Comments Operations ---

    def add_comment(self, layout_id: str, user_id: str, creator_name: str, content: str) -> Dict[str, Any]:
        comment = {
            "layout_id": layout_id,
            "user_id": user_id,
            "creator_name": creator_name,
            "content": content, # We will sanitize output to prevent XSS
            "timestamp": datetime.datetime.utcnow()
        }
        res = self.comments_collection.insert_one(comment)
        comment["id"] = str(res.inserted_id)
        del comment["_id"]
        return comment

    def delete_comment(self, comment_id: str, user_id: str) -> bool:
        try:
            res = self.comments_collection.delete_one({"_id": ObjectId(comment_id), "user_id": user_id})
            return res.deleted_count > 0
        except Exception:
            return False

    def get_layout_comments(self, layout_id: str) -> List[Dict[str, Any]]:
        cursor = self.comments_collection.find({"layout_id": layout_id}).sort("timestamp", -1)
        comments = []
        for item in cursor:
            item["id"] = str(item["_id"])
            del item["_id"]
            comments.append(item)
        return comments

    # --- Ratings Operations ---

    def add_rating(self, layout_id: str, user_id: str, rating: int) -> bool:
        self.ratings_collection.update_one(
            {"layout_id": layout_id, "user_id": user_id},
            {"$set": {"rating": rating, "timestamp": datetime.datetime.utcnow()}},
            upsert=True
        )
        return True

    def get_layout_rating_stats(self, layout_id: str) -> Dict[str, Any]:
        cursor = list(self.ratings_collection.find({"layout_id": layout_id}))
        if not cursor:
            return {"average": 0.0, "count": 0}
        
        ratings_sum = sum(item["rating"] for item in cursor)
        count = len(cursor)
        return {
            "average": round(ratings_sum / count, 1),
            "count": count
        }

    def get_user_rating_for_layout(self, layout_id: str, user_id: str) -> int:
        rating = self.ratings_collection.find_one({"layout_id": layout_id, "user_id": user_id})
        return rating["rating"] if rating else 0
