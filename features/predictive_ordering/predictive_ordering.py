from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict
import statistics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')

# Connect to MongoDB
client = MongoClient(MONGODB_CONNECTION_STRING, server_api=ServerApi('1'))
db = client[MONGODB_DATABASE]

# Collections
invoices_col = db['invoices']
items_col = db['items']
customers_col = db['customers']

class PredictiveOrderingSystem:
    def __init__(self):
        self.patterns_cache = {}
        
    def get_sap_customers(self):
        """Get all SAP customers (CardCode starting with 'C')"""
        try:
            sap_customers = customers_col.find({"CardCode": {"$regex": "^C"}})
            return list(sap_customers)
        except Exception as e:
            print(f"Error getting SAP customers: {e}")
            return []
    
    def analyze_customer_patterns(self, customer_id):
        """Analyze reorder patterns for a specific customer"""
        try:
            # Calculate date 1 year ago for filtering
            one_year_ago = datetime.now() - timedelta(days=365)
            
            # Get all invoices for this customer from last 1 year only
            customer_invoices = invoices_col.find({
                "CardCode": customer_id,
                "DocDate": {"$gte": one_year_ago}
            })
            
            # Group by ItemCode
            item_orders = defaultdict(list)
            
            for invoice in customer_invoices:
                if 'DocumentLines' in invoice and invoice['DocumentLines']:
                    for line in invoice['DocumentLines']:
                        item_code = line.get('ItemCode')
                        if item_code:
                            # Convert date to datetime if it's a string
                            doc_date = invoice.get('DocDate')
                            if isinstance(doc_date, str):
                                doc_date = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                            elif hasattr(doc_date, 'date'):
                                doc_date = doc_date
                            else:
                                continue
                                
                            item_orders[item_code].append({
                                'date': doc_date,
                                'quantity': line.get('Quantity', 0),
                                'price': line.get('Price', 0),
                                'doc_num': invoice.get('DocNum')
                            })
            
            # Filter items with 2+ orders only
            filtered_items = {item_code: orders for item_code, orders in item_orders.items() 
                            if len(orders) >= 2}
            
            if not filtered_items:
                return {}
            
            # BATCH QUERY: Get all item details in one query
            item_codes = list(filtered_items.keys())
            all_items = list(items_col.find({"ItemCode": {"$in": item_codes}}))
            
            # Create lookup dictionary for fast access
            items_lookup = {item['ItemCode']: item for item in all_items}
            
            # Calculate patterns for each item
            patterns = {}
            for item_code, orders in filtered_items.items():
                # Check if item is valid (only suggest valid items)
                item = items_lookup.get(item_code)
                if not item or item.get('Valid') != 'tYES':
                    continue  # Skip invalid items
                
                # Sort by date
                orders.sort(key=lambda x: x['date'])
                
                # Calculate intervals between orders
                intervals = []
                quantities = []
                prices = []
                
                for i in range(1, len(orders)):
                    interval = (orders[i]['date'] - orders[i-1]['date']).days
                    intervals.append(interval)
                    quantities.append(orders[i-1]['quantity'])
                    prices.append(orders[i-1]['price'])
                
                # Add last order quantity and price
                quantities.append(orders[-1]['quantity'])
                prices.append(orders[-1]['price'])
                
                if intervals:
                    # Get current inventory info from the lookup
                    current_stock = item.get('QuantityOnStock', 0)
                    item_name = item.get('ItemName', 'Unknown')
                    
                    patterns[item_code] = {
                        'avg_interval': round(statistics.mean(intervals)),
                        'median_interval': round(statistics.median(intervals)),
                        'min_interval': min(intervals),
                        'max_interval': max(intervals),
                        'avg_quantity': statistics.mean(quantities),
                        'avg_price': round(statistics.mean(prices), 2),
                        'last_order_date': orders[-1]['date'],
                        'total_orders': len(orders),
                        'current_stock': current_stock,
                        'item_name': item_name,
                        'intervals': intervals
                    }
            
            return patterns
            
        except Exception as e:
            print(f"Error analyzing patterns for customer {customer_id}: {e}")
            return {}
    
    def get_item_inventory(self, item_code):
        """Get current inventory for an item"""
        try:
            item = items_col.find_one({"ItemCode": item_code})
            if item:
                # Check if item is valid (only suggest valid items)
                if item.get('Valid') != 'tYES':
                    return None  # Skip invalid items
                
                return {
                    'quantity_on_stock': item.get('QuantityOnStock', 0),
                    'item_name': item.get('ItemName', ''),
                    'item_code': item.get('ItemCode', '')
                }
            return None
        except Exception as e:
            print(f"Error getting inventory for item {item_code}: {e}")
            return None
    
    def generate_suggestions(self, customer_id):
        """Generate smart cart suggestions for a customer"""
        try:
            # Get customer patterns (now includes inventory data)
            patterns = self.analyze_customer_patterns(customer_id)
            
            suggestions = []
            current_date = datetime.now()
            
            for item_code, pattern in patterns.items():
                # Inventory data is already available in pattern
                current_stock = pattern['current_stock']
                item_name = pattern['item_name']
                
                days_since_last_order = (current_date - pattern['last_order_date']).days
                avg_interval = pattern['avg_interval']
                avg_quantity = pattern['avg_quantity']
                
                # Only suggest for reasonable intervals (weekly to monthly)
                if avg_interval < 7 or avg_interval > 90:  # Between 1 week and 3 months
                    continue
                
                # Suggestion 1: "Add your usual [ItemName]" - 3-10 days overdue window
                # Window: avg_interval + 6 to avg_interval + 10 days (meaningful overdue period)
                if (days_since_last_order >= avg_interval + 3 and 
                    days_since_last_order <= avg_interval + 10):
                    suggestions.append({
                        'type': 'usual_reorder',
                        'message': f"Add your usual {item_name}",
                        'item_code': item_code,
                        'item_name': item_name,
                        'reason': f"You typically order this every {avg_interval} days. It's been {days_since_last_order} days since your last order.",
                        'priority': 'high' if days_since_last_order > avg_interval + 8 else 'medium'
                    })
                
                # Suggestion 2: "Stock running low on [ItemName]?"
                stock_threshold = avg_quantity * 2
                
                # Handle negative stock (over-sold situation) - but acknowledge sourcing capability
                if current_stock < 0:
                    suggestions.append({
                        'type': 'low_stock',
                        'message': f"{item_name}",
                        'item_code': item_code,
                        'item_name': item_name,
                        'reason': f"Your typical order: {avg_quantity:.1f} units.",
                        'priority': 'medium'
                    })
                elif current_stock < stock_threshold and days_since_last_order <= 90:
                    suggestions.append({
                        'type': 'low_stock',
                        'message': f"Stock running low on {item_name}?",
                        'item_code': item_code,
                        'item_name': item_name,
                        'reason': f"Your typical order: {avg_quantity:.1f} units.",
                        'priority': 'high' if current_stock < avg_quantity else 'medium'
                    })
            
            # Group suggestions by type and ensure minimum 3 items per category
            grouped_suggestions = {}
            for suggestion in suggestions:
                if suggestion['type'] not in grouped_suggestions:
                    grouped_suggestions[suggestion['type']] = []
                grouped_suggestions[suggestion['type']].append(suggestion)
            
            # Sort each group by priority and ensure at least 3 items
            top_suggestions = []
            for suggestion_type, type_suggestions in grouped_suggestions.items():
                # Sort by priority (high -> medium -> low)
                type_suggestions.sort(key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)
                
                # Take at least 3 items, or all if less than 3
                min_items = min(3, len(type_suggestions))
                top_suggestions.extend(type_suggestions[:min_items])
            
            return top_suggestions
            
        except Exception as e:
            print(f"Error generating suggestions for customer {customer_id}: {e}")
            return []
    
    def get_customer_predictions(self, customer_id):
        """Get comprehensive predictions for a customer"""
        try:
            patterns = self.analyze_customer_patterns(customer_id)
            suggestions = self.generate_suggestions(customer_id)
            
            # Get customer info
            customer = customers_col.find_one({"CardCode": customer_id})
            customer_info = {
                'card_code': customer.get('CardCode', ''),
                'card_name': customer.get('CardName', ''),
                'customer_type': customer.get('customerType', ''),
                'country': customer.get('address', {}).get('country', '')
            } if customer else {}
            
            return {
                'customer_info': customer_info,
                'patterns': patterns,
                'suggestions': suggestions,
                'total_items_analyzed': len(patterns),
                'total_suggestions': len(suggestions),
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting predictions for customer {customer_id}: {e}")
            return {}

# Global instance
predictive_system = PredictiveOrderingSystem()

def get_predictive_recommendations(customer_id):
    """Main function to get predictive recommendations"""
    return predictive_system.get_customer_predictions(customer_id)

def get_all_sap_predictions():
    """Get predictions for all SAP customers"""
    sap_customers = predictive_system.get_sap_customers()
    all_predictions = {}
    
    for customer in sap_customers[:10]:  # Limit to first 10 for testing
        customer_id = customer.get('CardCode')
        if customer_id:
            predictions = predictive_system.get_customer_predictions(customer_id)
            all_predictions[customer_id] = predictions
    
    return all_predictions 