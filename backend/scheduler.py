import asyncio
from database import document_collection
from datetime import datetime, timezone
import os

async def cleanup_expired_documents():
    print("Started background cleanup task...")
    while True:
        try:
            now = datetime.now(timezone.utc).timestamp()
            # Find all documents where expiry_time < current time
            cursor = document_collection.find({"expiry_time": {"$lt": now}})
            async for doc in cursor:
                doc_id = doc["_id"]
                file_path = doc["filepath"]
                
                # Delete physical file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted expired file: {file_path}")
                
                # Delete from database
                await document_collection.delete_one({"_id": doc_id})
                print(f"Deleted expired DB record: {doc_id}")
                
        except Exception as e:
            print(f"Error in cleanup script: {e}")
            
        # Run every 5 seconds for snappy updates
        await asyncio.sleep(5)
