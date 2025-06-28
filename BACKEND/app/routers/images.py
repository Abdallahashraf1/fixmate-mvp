from fastapi import APIRouter, HTTPException
from typing import List
#from bson import ObjectId
import io, base64
from PIL import Image, ImageOps

from app.db import mongo_client
from app.models import ImageRequest

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/", response_model=List[dict])
def fetch_images(req: ImageRequest):
    out = []
    col = mongo_client[req.make.lower()][req.model]
    for img_id in req.image_ids:
        doc = col.find_one({"_id": img_id})
        if not doc or "data" not in doc:
            continue
        img = Image.open(io.BytesIO(doc["data"]))
        if img.mode in ("1","L","P"):
            img = ImageOps.invert(img.convert("RGB"))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        out.append({
            "id": img_id,
            "page": doc.get("page", 0),
            "source": doc.get("pdf", ""),
            "data": b64
        })
    if not out:
        raise HTTPException(status_code=404, detail="No images found")
    return out