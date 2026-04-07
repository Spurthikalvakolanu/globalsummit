import os
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import document_collection, document_helper
from scheduler import cleanup_expired_documents
import asyncio
from datetime import datetime, timezone
from bson import ObjectId

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_expired_documents())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    rule: str = Form(...)
):
    try:
        now = datetime.now(timezone.utc).timestamp()
        
        if rule == "1min":
            expiry_time = now + 60
            rule_name = "Demo - 1 Min Expiry"
        elif rule == "24h":
            expiry_time = now + (24 * 3600)
            rule_name = "Strict - 24 Hrs Expiry"
        else:
            raise HTTPException(status_code=400, detail="Invalid rule")

        file_location = os.path.join(UPLOAD_DIR, file.filename)
        
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        document = {
            "filename": file.filename,
            "filepath": file_location,
            "upload_time": now,
            "expiry_time": expiry_time,
            "status": "Active",
            "rule": rule_name
        }
        
        new_doc = await document_collection.insert_one(document)
        created_doc = await document_collection.find_one({"_id": new_doc.inserted_id})
        
        return document_helper(created_doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents():
    documents = []
    async for doc in document_collection.find():
        documents.append(document_helper(doc))
    # sort by expiry time ascending
    documents.sort(key=lambda x: x["expiry_time"])
    return {"data": documents}
    
@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        doc = await document_collection.find_one({"_id": ObjectId(doc_id)})
        if doc:
            if os.path.exists(doc["filepath"]):
                os.remove(doc["filepath"])
            await document_collection.delete_one({"_id": ObjectId(doc_id)})
            return {"message": "Document deleted directly"}
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
