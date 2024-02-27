import os
import json
import pymongo

from datetime import datetime
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

db = MongoClient(os.environ.get("MONGO_URI"))["youtube_data"]

def insert_images_to_mongo():
    collection = db["images"]
    collection.create_index([("video_id", pymongo.DESCENDING)])

    image_dir_path = "./Image_dir"
    if os.path.exists(image_dir_path) and os.listdir(image_dir_path):
        for folder_name in os.listdir(image_dir_path):
            folder_path = os.path.join(image_dir_path, folder_name)
            print(folder_path)
            if os.path.isdir(folder_path) and os.listdir(folder_path):
                for image_name in os.listdir(folder_path):
                    image_path = os.path.join(folder_path, image_name)
                    with open(image_path, "rb") as image_file:
                        collection.insert_one({
                            "video_id": folder_name.split("_")[-1],
                            "created_at": datetime.now(),
                            "image_id": open(image_path, "rb").read()
                        })
def create_metadata():
    collection = db["metadata"]
    collection.create_index([("video_id", pymongo.DESCENDING)])

    if os.path.exists("metadata"):
        for file in os.listdir("metadata"):
            with open(f"metadata/{file}", "r") as f:
                data = json.load(f)
                for _ in data:
                    _['created_at'] = datetime.now()
                    collection.insert_one(_)