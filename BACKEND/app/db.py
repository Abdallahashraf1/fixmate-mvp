# db.py:
import os
import certifi
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from pymongo import MongoClient

load_dotenv()

OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MONGO_URI        = os.getenv("MONGO_URI")

openai_client    = OpenAI(api_key=OPENAI_API_KEY)
pinecone_client  = Pinecone(api_key=PINECONE_API_KEY)
mongo_client     = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
sessions_col     = mongo_client["FixMate"]["sessions"]
history_col      = mongo_client["FixMate"]["chat_history"]