from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
from collections import Counter
from difflib import SequenceMatcher
import re

MONGODB_CONNECTION_STRING = "mongodb+srv://sohaibsipra869:nvidia940MX@cluster0.q1so4va.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DATABASE = "test"

# Connect to MongoDB
client = MongoClient(MONGODB_CONNECTION_STRING, server_api=ServerApi('1'))
db = client[MONGODB_DATABASE]

# Access collections
customers_col = db["customers"]
invoices_col = db["invoices"]
items_col = db["items"]

# 1. Count SAP customers (CardCode starts with 'C' and customerType is 'sap')
sap_customers_count = customers_col.count_documents({
    "CardCode": {"$regex": r"^C\\d+"},
    "customerType": "sap"
})
print(f"Number of SAP customers: {sap_customers_count}")

# 2. Print a sample invoice
def print_sample_invoice():
    sample_invoice = invoices_col.find_one()
    if sample_invoice:
        print("Sample Invoice:")
        print(sample_invoice)
    else:
        print("No invoices found.")

# 3. Print a sample item
def print_sample_item():
    sample_item = items_col.find_one()
    if sample_item:
        print("Sample Item:")
        print(sample_item)
    else:
        print("No items found.")

def get_customer_order_history(card_code, invoices_col):
    """Return a list of all items (ItemCode) ordered by the customer, with quantities, dates, and invoice details."""
    order_history = []
    for invoice in invoices_col.find({"CardCode": card_code}):
        doc_date = invoice.get("DocDate")
        doc_num = invoice.get("DocNum")
        doc_total = invoice.get("DocTotal", 0)
        
        for line in invoice.get("DocumentLines", []):
            quantity = line.get("Quantity", 0)
            # Only include items with positive quantities (actual purchases)
            if quantity and float(quantity) > 0:
                order_history.append({
                    "ItemCode": line.get("ItemCode"),
                    "ItemDescription": line.get("ItemDescription"),
                    "Quantity": quantity,
                    "Price": line.get("Price", 0),
                    "LineTotal": line.get("LineTotal", 0),
                    "DocDate": doc_date,
                    "DocNum": doc_num,
                    "DocTotal": doc_total,
                    "InvoiceID": str(invoice.get("_id"))
                })
    

    
    return order_history

def get_item_details(item_codes, items_col):
    """Get detailed information for items including category and group."""
    if not item_codes:
        return {}
    
    item_details = {}
    # Use a single query to get all item details at once (only valid items)
    items = list(items_col.find({
        "ItemCode": {"$in": item_codes},
        "Valid": "tYES"  # Only valid items
    }))
    
    for item in items:
        item_details[item["ItemCode"]] = {
            "ItemName": item.get("ItemName", ""),
            "ItemsGroupCode": item.get("ItemsGroupCode", 0),
            "U_SubCategory": item.get("U_SubCategory", ""),
            "U_cat_lev_2": item.get("U_cat_lev_2", ""),
            "QuantityOnStock": item.get("QuantityOnStock", 0),
            "ItemPrices": item.get("ItemPrices", [])
        }
    return item_details

def find_similar_items_by_name(item_code, items_col, item_name, purchased_codes=None, limit=5):
    """Find items with similar names using database queries for better performance."""
    if not item_name:
        return []
    
    # Extract key words from item name for better matching
    words = re.findall(r'\b\w+\b', item_name.lower())
    if not words:
        return []
    
    # Use only the first 2 most significant words to reduce query complexity
    significant_words = [word for word in words[:2] if len(word) > 3]
    
    if not significant_words:
        return []
    
    # Build query to find items with similar words in name
    name_conditions = []
    for word in significant_words:
        name_conditions.append({"ItemName": {"$regex": word, "$options": "i"}})
    
    # Build the main query
    query = {
        "ItemCode": {"$ne": item_code},
        "QuantityOnStock": {"$gt": 0},  # Only in-stock items
        "Valid": "tYES",  # Only valid items
        "$or": name_conditions
    }
    
    # Exclude already purchased items
    if purchased_codes:
        query["ItemCode"]["$nin"] = list(purchased_codes)
    
    # Execute query with smaller limit for better performance
    candidates = list(items_col.find(query).limit(limit + 2))  # Reduced from limit * 2
    
    # Apply fuzzy matching to the results
    results = []
    for item in candidates:
        name = item.get("ItemName", "")
        if name:
            similarity = SequenceMatcher(None, item_name.lower(), name.lower()).ratio()
            if similarity > 0.4:  # Slightly higher threshold for better quality
                results.append({
                    "ItemCode": item["ItemCode"],
                    "ItemName": name,
                    "QuantityOnStock": item.get("QuantityOnStock", 0),
                    "Tag": "Name similarity",
                    "similarity": similarity
                })
    
    # Sort by similarity and return top results
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:limit]

def find_similar_items_by_code(item_code, items_col, purchased_codes=None, limit=5):
    """Find items with similar category (ItemsGroupCode) using database queries."""
    if not item_code:
        return []
    
    # First, get the current item's category (ItemsGroupCode) - only if valid
    current_item = items_col.find_one({
        "ItemCode": item_code,
        "Valid": "tYES"  # Only valid items
    })
    if not current_item:
        return []
    
    current_category = current_item.get("ItemsGroupCode")
    if not current_category:
        return []
    
    # Build query to find items in the same category
    query = {
        "ItemsGroupCode": current_category,
        "ItemCode": {"$ne": item_code},
        "QuantityOnStock": {"$gt": 0},
        "Valid": "tYES"  # Only valid items
    }
    
    # Exclude already purchased items
    if purchased_codes:
        query["ItemCode"]["$nin"] = list(purchased_codes)
    
    # Execute query with limit
    results = []
    for item in items_col.find(query).limit(limit):
        results.append({
            "ItemCode": item["ItemCode"],
            "ItemName": item.get("ItemName", ""),
            "QuantityOnStock": item.get("QuantityOnStock", 0),
            "Tag": "Category similarity"
        })
    
    return results



def analyze_order_frequency(order_history):
    """Analyze order frequency and return top items with their purchase history."""
    if not order_history:
        return []
    
    # Count total quantities per item
    item_counts = Counter()
    item_descriptions = {}
    item_invoices = {}
    
    for order in order_history:
        item_code = order["ItemCode"]
        quantity = float(order["Quantity"]) if order["Quantity"] is not None else 0
        
        item_counts[item_code] += quantity
        item_descriptions[item_code] = order["ItemDescription"]
        
        if item_code not in item_invoices:
            item_invoices[item_code] = []
        
        item_invoices[item_code].append({
            "DocNum": order["DocNum"],
            "DocDate": order["DocDate"],
            "Quantity": order["Quantity"],
            "Price": order["Price"]
        })
    
    # Get top items by total quantity
    top_items = item_counts.most_common(10)  # Top 10 items
    

    
    return [
        {
            "ItemCode": item_code,
            "ItemDescription": item_descriptions.get(item_code, "Unknown"),
            "TotalQuantity": quantity,
            "Invoices": sorted(item_invoices.get(item_code, []), 
                             key=lambda x: x["DocDate"], reverse=True)[:5]  # Last 5 invoices
        }
        for item_code, quantity in top_items
    ]

def get_personalized_recommendations(card_code, invoices_col, items_col):
    """Get personalized recommendations based on order history with two similarity filters."""
    # Get customer's order history
    order_history = get_customer_order_history(card_code, invoices_col)
    
    if not order_history:
        return {
            "message": "No order history found for this customer.",
            "recommendations": []
        }
    
    # Analyze order frequency
    frequent_items = analyze_order_frequency(order_history)
    
    # Get detailed item information
    item_codes = [item["ItemCode"] for item in frequent_items]
    item_details = get_item_details(item_codes, items_col)
    
    # Add inventory info and similar items to recommendations
    recommendations = []
    purchased_codes = set(item["ItemCode"] for item in frequent_items)
    
    # Process more items initially to ensure we get 5 recommendations after filtering
    items_processed = 0
    max_items_to_process = 15  # Process up to 15 items to find 5 with similar items
    
    for item in frequent_items:
        if len(recommendations) >= 5 or items_processed >= max_items_to_process:
            break
            
        item_code = item["ItemCode"]
        details = item_details.get(item_code, {})
        item_name = details.get("ItemName", item["ItemDescription"])
        
        # Find similar items for all items until we have 5 recommendations
        similar_by_name = find_similar_items_by_name(item_code, items_col, item_name, purchased_codes=purchased_codes, limit=3)
        similar_by_code = find_similar_items_by_code(item_code, items_col, purchased_codes=purchased_codes, limit=3)
        
        in_stock = details.get("QuantityOnStock", 0)
        
        # Only add items that have at least one similar item (by name OR code)
        if similar_by_name or similar_by_code:
            recommendations.append({
                **item,
                "InStock": in_stock,
                "Available": in_stock > 0,  # Set availability based on stock
                "SimilarItemsByName": similar_by_name,
                "SimilarItemsByCode": similar_by_code,
                "Tag": "Based on purchase history"
            })
        
        items_processed += 1
    
    return {
        "message": f"Based on your order history, you usually order:",
        "recommendations": recommendations
    }

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 PERSONALIZED RECOMMENDATION SYSTEM")
    print("=" * 80)
    
    # Ask for customer ID
    while True:
        customer_id = input("\n🔍 Enter Customer ID (CardCode): ").strip()
        if customer_id:
            break
        print("❌ Please enter a valid Customer ID.")
    
    print("\n" + "=" * 80)
    
    # Get customer information
    customer_info = customers_col.find_one({"CardCode": customer_id})
    if customer_info:
        print(f"\n👤 CUSTOMER: {customer_info.get('CardName', 'Unknown')} ({customer_id})")
        print(f"📍 Location: {customer_info.get('address', {}).get('city', 'Unknown')}, {customer_info.get('address', {}).get('country', 'Unknown')}")
        print(f"📞 Phone: {customer_info.get('phoneNumber', 'Not provided')}")
        print(f"🏷️  Type: {customer_info.get('customerType', 'Unknown')}")
    else:
        print(f"\n👤 CUSTOMER: {customer_id} (Customer info not found)")
    
    print("\n" + "=" * 80)
    
    # Get recommendations
    recommendations = get_personalized_recommendations(customer_id, invoices_col, items_col)
    
    if recommendations['recommendations']:
        print(f"\n📊 RECOMMENDATION ANALYSIS")
        print(f"💡 {recommendations['message']}")
        print("\n" + "-" * 80)
        
        for i, rec in enumerate(recommendations['recommendations'], 1):
            status_icon = "✅" if rec['Available'] else "❌"
            status_text = "IN STOCK" if rec['Available'] else "OUT OF STOCK"
            
            print(f"\n{i}. 🛍️  {rec['ItemDescription']}")
            print(f"   📦 Product Code: {rec['ItemCode']}")
            print(f"   📈 Your Order History: {rec['TotalQuantity']} units total")
            print(f"   📊 Current Stock: {rec['InStock']} units")
            print(f"   {status_icon} Status: {status_text}")
            
            # Show invoice details
            if rec['Invoices']:
                print(f"   📋 Purchase History:")
                for inv in rec['Invoices'][:3]:  # Show last 3 purchases
                    date_str = inv['DocDate'].strftime("%Y-%m-%d") if inv['DocDate'] else "Unknown"
                    print(f"      • Invoice #{inv['DocNum']} ({date_str}): {inv['Quantity']} units @ €{inv['Price']:.2f}")
                if len(rec['Invoices']) > 3:
                    print(f"      • ... and {len(rec['Invoices']) - 3} more purchases")
            
            # Explain why it was recommended
            if rec['TotalQuantity'] > 10:
                reason = "You frequently order this item"
            elif rec['TotalQuantity'] > 5:
                reason = "You regularly purchase this product"
            else:
                reason = "You have ordered this item before"
            
            print(f"   💭 Why Recommended: {reason}")
            
            # Show similar items
            if rec['SimilarItemsByName']:
                print(f"   🔍 Similar Items You Might Like (Name):")
                for j, similar in enumerate(rec['SimilarItemsByName'], 1):
                    similar_status = "✅" if similar['QuantityOnStock'] > 0 else "❌"
                    print(f"      {j}. {similar['ItemName']} ({similar['ItemCode']}) {similar_status}")
            
            if rec['SimilarItemsByCode']:
                print(f"   🔍 Similar Items You Might Like (Category):")
                for j, similar in enumerate(rec['SimilarItemsByCode'], 1):
                    similar_status = "✅" if similar['QuantityOnStock'] > 0 else "❌"
                    print(f"      {j}. {similar['ItemName']} ({similar['ItemCode']}) {similar_status}")
            
            print("-" * 80)
    else:
        print(f"\n❌ {recommendations['message']}")
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATION SYSTEM COMPLETE")
    print("=" * 80)
