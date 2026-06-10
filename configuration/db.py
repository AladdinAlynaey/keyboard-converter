import pymongo
from pymongo import MongoClient
from configuration.config import Config, logger

class DatabaseManager:
    _client = None
    _db = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                cls._client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
                # Force a connection check
                cls._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB!")
            except Exception as e:
                logger.critical(f"Failed to connect to MongoDB at {Config.MONGO_URI}: {e}")
                raise e
        return cls._client

    @classmethod
    def get_db(cls):
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[Config.MONGO_DB]
            cls.initialize_indexes()
        return cls._db

    @classmethod
    def initialize_indexes(cls):
        db = cls._db
        logger.info("Initializing MongoDB indexes...")
        try:
            # Users indexes
            db.users.create_index("email", unique=True)
            db.users.create_index("google_id", sparse=True)
            
            # Layouts indexes
            db.layouts.create_index([("user_id", pymongo.ASCENDING), ("name", pymongo.ASCENDING)])
            db.layouts.create_index("is_public")
            
            # Published layouts indexes
            # Text index for search
            try:
                db.published_layouts.drop_index("name_text_description_text_tags_text")
            except Exception:
                pass
            db.published_layouts.create_index([
                ("name", pymongo.TEXT),
                ("description", pymongo.TEXT),
                ("tags", pymongo.TEXT)
            ], weights={"name": 10, "description": 5, "tags": 2}, language_override="none")
            
            db.published_layouts.create_index("downloads")
            db.published_layouts.create_index("likes")
            db.published_layouts.create_index("created_at")
            
            # History indexes
            db.history.create_index([("user_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
            
            # Favorites indexes
            db.favorites.create_index([("user_id", pymongo.ASCENDING), ("layout_id", pymongo.ASCENDING)], unique=True)
            
            # Comments indexes
            db.comments.create_index([("layout_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
            
            # Ratings indexes
            db.ratings.create_index([("layout_id", pymongo.ASCENDING), ("user_id", pymongo.ASCENDING)], unique=True)
            
            # Sessions/refresh tokens tracking indexes
            db.sessions.create_index([("user_id", pymongo.ASCENDING), ("jti", pymongo.ASCENDING)], unique=True)
            db.sessions.create_index("expires_at", expireAfterSeconds=0) # Automatically clean up expired sessions
            
            logger.info("Indexes successfully initialized!")
        except Exception as e:
            logger.error(f"Failed to initialize database indexes: {e}")

# Helper function
def get_db():
    return DatabaseManager.get_db()
