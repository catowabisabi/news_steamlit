from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

connection_string = os.getenv('MONGODB_CONNECTION_STRING')
# connection_string = "mongodb://localhost:27017/mydatabase" # Or your Atlas connection string
client = MongoClient(connection_string)

# You can then access the database and collections
db = client.mydatabase
collection = db.mycollection

print(db.list_collection_names())
print(collection)