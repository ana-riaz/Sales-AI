from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')

# Connect to MongoDB
client = MongoClient(MONGODB_CONNECTION_STRING, server_api=ServerApi('1'))
db = client[MONGODB_DATABASE]

# Access collections
customers_col = db["customers"]
invoices_col = db["invoices"]
items_col = db["items"]

def setup_indexes():
    """Set up database indexes for better performance."""
    print("Setting up database indexes...")
    
    try:
        # Customers collection indexes
        customers_col.create_index([("CardCode", ASCENDING)], unique=True)
        customers_col.create_index([("customerType", ASCENDING)])
        print("✅ Customers indexes created")
        
        # Invoices collection indexes
        invoices_col.create_index([("CardCode", ASCENDING)])
        invoices_col.create_index([("DocDate", ASCENDING)])
        invoices_col.create_index([("DocNum", ASCENDING)])
        print("✅ Invoices indexes created")
        
        # Items collection indexes
        items_col.create_index([("ItemCode", ASCENDING)], unique=True)
        items_col.create_index([("ItemName", TEXT)])  # Text index for name searches
        items_col.create_index([("U_SubCategory", ASCENDING)])
        items_col.create_index([("ItemsGroupCode", ASCENDING)])
        items_col.create_index([("QuantityOnStock", ASCENDING)])
        print("✅ Items indexes created")
        
        print("\n🎉 All indexes created successfully!")
        print("Performance should be significantly improved now.")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")

if __name__ == "__main__":
    setup_indexes() 