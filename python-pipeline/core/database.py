from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Use a properly formatted connection string
uri = "mongodb+srv://himathnimpura:himathavenge@cluster0.bjaku.mongodb.net/User_Details?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["infact_db"]  

# Collections
article_collection = db["articles"]  
clusters_collection = db["clusters"]
subscribers_collection = db["subscribers"]

# Check if connection is successful
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")
