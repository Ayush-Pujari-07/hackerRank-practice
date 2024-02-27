import base64
import os
import motor.motor_asyncio

from pydantic import BaseModel
from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Assuming MongoDB is running on the default port on localhost
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get('MONGO_URI'))
db = client['youtube_data']

class FetchDataForm(BaseModel):
    data_type: str
    data_input: str

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/fetch-data/", response_class=HTMLResponse)
async def fetch_data(form_data: FetchDataForm = Form(...)):
    
    return 
    
@app.post("/fetch-data/", response_class=HTMLResponse)
async def fetch_data(data_type: str = Form(...), data_input: str = Form(...)):
    return f"Data Type: {data_type}, Data Input: {data_input}"

@app.get("/images/{video_id}", response_class=HTMLResponse)
async def read_root(request: Request, video_id: str):
    # Fetch all images from the collection
    images_cursor = db["images"].find({'video_id': video_id})
    images_count = await db["images"].count_documents({'video_id': video_id})

    images = await images_cursor.to_list(length=images_count)
    for img in images:
        if 'image' in img:
            img['image_base64'] = base64.b64encode(
                img['image']).decode('utf-8')
        else:
            img['image_base64'] = None
    return templates.TemplateResponse("display_images.html", {"request": request, "images": images})


@app.post("/delete-selected-images/")
async def delete_selected_images(request: Request, image_ids: list = Form(...)):
    for image_id in image_ids:
        await db["images"].delete_one({"_id": ObjectId(image_id)})
    return {"message": "Selected images have been deleted successfully."}
