import os

from pymongo import MongoClient
from dotenv import find_dotenv, load_dotenv
from pymongo.errors import ConfigurationError, NetworkTimeout

load_dotenv(find_dotenv())

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

collection = client["Data_extraction_DB"]["image_data"]

def store_image_to_mongodb(image_path, metadata):
    """
    Stores an image to the MongoDB collection along with its metadata.
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = image_file.read()
        
        # Creating a document to insert into the collection
        document = {
            "video_id": metadata["video_id"],
            "image": encoded_image,
        }
        
        # Inserting the document into the collection
        collection.insert_one(document)
        print(f"Image stored successfully with metadata: {metadata}")
        
    except NetworkTimeout as e:
        print(f"Failed to store image. Error: {e}")



