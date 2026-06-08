import certifi
from openai import OpenAI
from pinecone import Pinecone
from pymongo import MongoClient

from app.config import settings

openai_client    = OpenAI(api_key=settings.openai_api_key)
pinecone_client  = Pinecone(api_key=settings.pinecone_api_key)
mongo_client     = MongoClient(settings.mongo_uri, tls=True, tlsCAFile=certifi.where())
sessions_col     = mongo_client["FixMate"]["sessions"]
history_col      = mongo_client["FixMate"]["chat_history"]
