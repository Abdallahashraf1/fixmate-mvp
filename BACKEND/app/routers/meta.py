#routers/meta.py :
from fastapi import APIRouter, Query
from app.db import pinecone_client, mongo_client

router = APIRouter(prefix="/meta", tags=["meta"])

@router.get("/makes", response_model=list[str])
def list_makes():
    return pinecone_client.list_indexes().names()

@router.get("/models", response_model=list[str])
def list_models(make: str = Query(..., description="Vehicle make")):
    db = mongo_client[make.lower()]
    return db.list_collection_names()