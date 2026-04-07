import motor.motor_asyncio
import os

MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.datagov
document_collection = database.get_collection("documents")

def document_helper(doc) -> dict:
    return {
        "id": str(doc["_id"]),
        "filename": doc["filename"],
        "filepath": doc["filepath"],
        "upload_time": doc["upload_time"],
        "expiry_time": doc["expiry_time"],
        "status": doc.get("status", "Active"),
        "rule": doc.get("rule", "Custom")
    }
