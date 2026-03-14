import pymongo
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
import os

class UpsellingEngine:
    def __init__(self, connection_string, database_name):
        """Initialize the upselling engine with MongoDB connection."""
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[database_name]
        self.deals_collection = self.db.deals
        self.items_collection = self.db.items
        self.invoices_collection = self.db.invoices
        self.customers_collection = self.db.customers
        
        # Create results directory if it doesn't exist
        self.results_dir = "features/upselling_cross_selling/analysis_results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def _create_name_to_itemcode_mapping(self):
        """Create a mapping from product names to item codes for deals analysis."""
        print("Creating product name to item code mapping...")
        
        # Get all valid items
        valid_items = list(self.items_collection.find({
            "Valid": "tYES"
        }, {
            "ItemCode": 1,
            "ItemName": 1
        }))
        
        # Create mapping (name -> itemCode)
        name_to_code = {}
        for item in valid_items:
            item_name = item.get('ItemName', '').strip()
            item_code = item.get('ItemCode', '').strip()
            if item_name and item_code:
                name_to_code[item_name] = item_code
        
        print(f"Created mapping for {len(name_to_code)} items")
        return name_to_code
    
    def analyze_deal_bundles(self):
        """Analyze deals to find product bundles and complementary items."""
        print("Analyzing deal bundles...")
        
        # Create name to item code mapping
        name_to_code = self._create_name_to_itemcode_mapping()
        
        # Get all deals with products
        deals_with_products = list(self.deals_collection.find({
            "products": {"$exists": True, "$ne": []}
        }))
        
        print(f"Found {len(deals_with_products)} deals with products")
        
        # Analyze bundle patterns
        bundle_patterns = defaultdict(int)
        item_frequency = Counter()
        complementary_items = defaultdict(Counter)
        
        for deal in deals_with_products:
            products = deal.get('products', [])
            if len(products) > 1:  # Only analyze deals with multiple products
                # Extract item codes from product names
                product_codes = []
                for product in products:
                    product_name = product.get('name', '').strip()
                    if product_name in name_to_code:
                        product_codes.append(name_to_code[product_name])
                
                if len(product_codes) > 1:
                    # Sort to ensure consistent pattern
                    product_codes.sort()
                    bundle_key = "|".join(product_codes)
                    bundle_patterns[bundle_key] += 1
                    
                    # Count individual item frequency
                    for item_code in product_codes:
                        item_frequency[item_code] += 1
                    
                    # Find complementary items
                    for i, item1 in enumerate(product_codes):
                        for j, item2 in enumerate(product_codes):
                            if i != j:
                                complementary_items[item1][item2] += 1
        
        print(f"Found {len(bundle_patterns)} bundle patterns")
        print(f"Found {len(item_frequency)} unique items in deals")
        
        return {
            'bundle_patterns': dict(bundle_patterns),
            'item_frequency': dict(item_frequency),
            'complementary_items': {k: dict(v) for k, v in complementary_items.items()}
        }
    
    def get_valid_items(self):
        """Get all valid items for recommendations."""
        valid_items = list(self.items_collection.find({
            "Valid": "tYES"
        }, {
            "ItemCode": 1,
            "ItemName": 1,
            "ItemsGroupCode": 1,
            "QuantityOnStock": 1,
            "ItemPrices": 1
        }))
        
        # Create item lookup dictionary
        items_lookup = {}
        for item in valid_items:
            items_lookup[item['ItemCode']] = {
                'name': item.get('ItemName', ''),
                'group': item.get('ItemsGroupCode', ''),
                'stock': item.get('QuantityOnStock', 0),
                'prices': item.get('ItemPrices', [])
            }
        
        return items_lookup
    
    def generate_recommendations(self, customer_id, customer_items=None):
        """Generate customer-specific upselling and cross-selling recommendations."""
        print(f"Generating recommendations for customer {customer_id}")
        
        # Validate customer is SAP
        customer_info = self.customers_collection.find_one({
            "CardCode": customer_id,
            "customerType": "sap",
            "status": "active"
        })
        
        if not customer_info:
            raise ValueError(f"Customer {customer_id} not found or not a valid SAP customer")
        
        # If no items provided, get customer's recent purchase history
        if not customer_items:
            customer_items = self.get_customer_purchase_history(customer_id)
            print(f"Retrieved {len(customer_items)} items from customer history")
        
        # Analyze deal patterns
        bundle_analysis = self.analyze_deal_bundles()
        valid_items = self.get_valid_items()
        
        recommendations = {
            'customer_info': {
                'card_code': customer_info.get('CardCode'),
                'card_name': customer_info.get('CardName'),
                'customer_type': customer_info.get('customerType'),
                'location': f"{customer_info.get('address', {}).get('city', 'Unknown')}, {customer_info.get('address', {}).get('country', 'Unknown')}"
            },
            'bundle_suggestions': [],
            'complementary_items': [],
            'popular_addons': [],
            'customer_specific_suggestions': [],
            'analysis_summary': {}
        }
        
        # Find bundle suggestions
        bundle_suggestions = self._find_bundle_suggestions(
            customer_items, bundle_analysis, valid_items, customer_id
        )
        recommendations['bundle_suggestions'] = bundle_suggestions
        
        # Find complementary items
        complementary_items = self._find_complementary_items(
            customer_items, bundle_analysis, valid_items, customer_id
        )
        recommendations['complementary_items'] = complementary_items
        
        # Find popular add-ons
        popular_addons = self._find_popular_addons(
            customer_items, bundle_analysis, valid_items, customer_id
        )
        recommendations['popular_addons'] = popular_addons
        
        # Find customer-specific suggestions based on their purchase patterns
        customer_specific = self._find_customer_specific_suggestions(
            customer_id, customer_items, bundle_analysis, valid_items
        )
        recommendations['customer_specific_suggestions'] = customer_specific
        
        # Add analysis summary
        recommendations['analysis_summary'] = {
            'total_bundles_analyzed': len(bundle_analysis['bundle_patterns']),
            'total_items_analyzed': len(bundle_analysis['item_frequency']),
            'customer_items_count': len(customer_items),
            'recommendations_generated': len(bundle_suggestions) + len(complementary_items) + len(popular_addons) + len(customer_specific)
        }
        
        # Save analysis results
        self._save_analysis_results(customer_id, recommendations)
        
        return recommendations
    
    def _find_bundle_suggestions(self, customer_items, bundle_analysis, valid_items, customer_id):
        """Find complete bundles that contain customer's items."""
        suggestions = []
        
        for bundle_pattern, frequency in bundle_analysis['bundle_patterns'].items():
            bundle_items = bundle_pattern.split('|')
            
            # Check if customer's items are part of this bundle
            customer_items_set = set(customer_items)
            bundle_items_set = set(bundle_items)
            
            if customer_items_set.intersection(bundle_items_set):
                # Find missing items from the bundle
                missing_items = bundle_items_set - customer_items_set
                
                if missing_items and frequency >= 2:  # Only suggest if bundle appears at least 2 times
                    # Find what customer already has from this bundle
                    customer_bundle_items = customer_items_set.intersection(bundle_items_set)
                    
                    # Get names for customer's bundle items
                    customer_bundle_item_names = []
                    for item_code in customer_bundle_items:
                        if item_code in valid_items:
                            customer_bundle_item_names.append({
                                'item_code': item_code,
                                'name': valid_items[item_code]['name']
                            })
                    
                    # Get complete deal information
                    complete_deal_items = []
                    for item_code in bundle_items:
                        if item_code in valid_items:
                            item_info = valid_items[item_code]
                            is_customer_item = item_code in customer_bundle_items
                            complete_deal_items.append({
                                'item_code': item_code,
                                'name': item_info['name'],
                                'stock': item_info['stock'],
                                'price': self._get_default_price(item_info['prices']),
                                'customer_has': is_customer_item
                            })
                    
                    suggestion = {
                        'type': 'bundle_completion',
                        'message': f"Complete this deal package! You have {len(customer_bundle_items)} out of {len(bundle_items)} items. Add {len(missing_items)} more to get the full bundle",
                        'missing_items': [],
                        'customer_bundle_items': list(customer_bundle_items),  # Items customer already has
                        'customer_bundle_item_names': customer_bundle_item_names,  # Names of items customer has
                        'complete_deal_items': complete_deal_items,  # All items in the deal with customer status
                        'bundle_frequency': frequency,
                        'total_bundle_items': len(bundle_items),
                        'customer_specific': True
                    }
                    
                    for item_code in missing_items:
                        if item_code in valid_items:
                            item_info = valid_items[item_code]
                            suggestion['missing_items'].append({
                                'item_code': item_code,
                                'name': item_info['name'],
                                'stock': item_info['stock'],
                                'price': self._get_default_price(item_info['prices'])
                            })
                    
                    if suggestion['missing_items']:
                        suggestions.append(suggestion)
        
        # Sort by frequency and limit results
        suggestions.sort(key=lambda x: x['bundle_frequency'], reverse=True)
        return suggestions[:5]
    
    def _find_complementary_items(self, customer_items, bundle_analysis, valid_items, customer_id):
        """Find items that are frequently bought with customer's items."""
        suggestions = []
        
        for customer_item in customer_items:
            if customer_item in bundle_analysis['complementary_items']:
                complementary = bundle_analysis['complementary_items'][customer_item]
                
                # Get top complementary items
                top_complementary = sorted(complementary.items(), key=lambda x: x[1], reverse=True)[:3]
                
                for item_code, frequency in top_complementary:
                    if item_code not in customer_items and item_code in valid_items and frequency >= 2:
                        item_info = valid_items[item_code]
                        # Get the name of the customer item for the message
                        customer_item_name = valid_items.get(customer_item, {}).get('name', customer_item)
                        suggestions.append({
                            'type': 'complementary',
                            'message': f"Often included with {customer_item_name} in deal packages",
                            'item_code': item_code,
                            'name': item_info['name'],
                            'stock': item_info['stock'],
                            'price': self._get_default_price(item_info['prices']),
                            'frequency': frequency,
                            'customer_specific': True
                        })
        
        # Remove duplicates and sort by frequency
        unique_suggestions = {}
        for suggestion in suggestions:
            key = suggestion['item_code']
            if key not in unique_suggestions or suggestion['frequency'] > unique_suggestions[key]['frequency']:
                unique_suggestions[key] = suggestion
        
        suggestions = list(unique_suggestions.values())
        suggestions.sort(key=lambda x: x['frequency'], reverse=True)
        return suggestions[:10]
    
    def _find_popular_addons(self, customer_items, bundle_analysis, valid_items, customer_id):
        """Find popular items that could be added to customer's order."""
        suggestions = []
        
        # Get most frequent items overall
        top_items = sorted(bundle_analysis['item_frequency'].items(), key=lambda x: x[1], reverse=True)
        
        for item_code, frequency in top_items[:20]:  # Check top 20 items
            if item_code not in customer_items and item_code in valid_items and frequency >= 3:
                item_info = valid_items[item_code]
                suggestions.append({
                    'type': 'popular_addon',
                    'message': f"Popular item - appears in {frequency} deal packages",
                    'item_code': item_code,
                    'name': item_info['name'],
                    'stock': item_info['stock'],
                    'price': self._get_default_price(item_info['prices']),
                    'frequency': frequency,
                    'customer_specific': True
                })
        
        return suggestions[:5]
    
    def _find_customer_specific_suggestions(self, customer_id, customer_items, bundle_analysis, valid_items):
        """Find customer-specific suggestions based on their purchase patterns and preferences."""
        suggestions = []
        
        # Get customer's purchase history to understand their preferences
        customer_invoices = list(self.invoices_collection.find({
            "CardCode": customer_id
        }, {
            "DocumentLines": 1,
            "DocDate": 1,
            "DocTotal": 1
        }).sort("DocDate", -1).limit(20))
        
        # Analyze customer's preferred categories
        customer_categories = {}
        for invoice in customer_invoices:
            for line in invoice.get('DocumentLines', []):
                item_code = line.get('ItemCode')
                if item_code in valid_items:
                    category = valid_items[item_code]['group']
                    if category not in customer_categories:
                        customer_categories[category] = 0
                    customer_categories[category] += 1
        
        # Find items in customer's preferred categories that they haven't bought
        if customer_categories:
            top_categories = sorted(customer_categories.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for category, count in top_categories:
                # Find items in this category that customer hasn't bought
                category_items = []
                for item_code, item_info in valid_items.items():
                    if (item_info['group'] == category and 
                        item_code not in customer_items and 
                        item_code in bundle_analysis['item_frequency']):
                        
                        frequency = bundle_analysis['item_frequency'][item_code]
                        if frequency >= 2:  # Only suggest items with some popularity
                            category_items.append({
                                'item_code': item_code,
                                'name': item_info['name'],
                                'stock': item_info['stock'],
                                'price': self._get_default_price(item_info['prices']),
                                'frequency': frequency
                            })
                
                # Sort by frequency and take top 2 from each category
                category_items.sort(key=lambda x: x['frequency'], reverse=True)
                for item in category_items[:2]:
                    suggestions.append({
                        'type': 'customer_specific',
                        'message': f"Based on your category preference (purchased {count} times) - this item is available in deal packages",
                        'item_code': item['item_code'],
                        'name': item['name'],
                        'stock': item['stock'],
                        'price': item['price'],
                        'frequency': item['frequency'],
                        'category': category,
                        'customer_specific': True
                    })
        
        # Find items similar to what customer frequently buys
        customer_item_frequency = {}
        for item in customer_items:
            if item in customer_item_frequency:
                customer_item_frequency[item] += 1
            else:
                customer_item_frequency[item] = 1
        
        # Find items in same categories as customer's frequent purchases
        frequent_items = sorted(customer_item_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for item_code, freq in frequent_items:
            if item_code in valid_items:
                category = valid_items[item_code]['group']
                
                # Find other items in same category
                for other_item_code, other_item_info in valid_items.items():
                    if (other_item_info['group'] == category and 
                        other_item_code not in customer_items and
                        other_item_code in bundle_analysis['item_frequency']):
                        
                        frequency = bundle_analysis['item_frequency'][other_item_code]
                        if frequency >= 2:
                            suggestions.append({
                                'type': 'customer_specific',
                                'message': f"Similar to {item_code} (you purchased {freq} times) - available in deal packages",
                                'item_code': other_item_code,
                                'name': other_item_info['name'],
                                'stock': other_item_info['stock'],
                                'price': self._get_default_price(other_item_info['prices']),
                                'frequency': frequency,
                                'category': category,
                                'customer_specific': True
                            })
                            break  # Only suggest one similar item per frequent item
        
        # Remove duplicates and limit results
        unique_suggestions = {}
        for suggestion in suggestions:
            key = suggestion['item_code']
            if key not in unique_suggestions:
                unique_suggestions[key] = suggestion
        
        suggestions = list(unique_suggestions.values())
        suggestions.sort(key=lambda x: x['frequency'], reverse=True)
        return suggestions[:8]
    
    def _get_default_price(self, prices):
        """Get default price from item prices."""
        if not prices:
            return 0
        
        # Try to get price from PriceList 1 (usually default)
        for price_info in prices:
            if price_info.get('PriceList') == 1:
                return price_info.get('Price', 0)
        
        # Fallback to first available price
        return prices[0].get('Price', 0) if prices else 0
    
    def _save_analysis_results(self, customer_id, recommendations):
        """Save analysis results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upselling_analysis_{customer_id}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, default=str)
        
        print(f"Analysis results saved to: {filepath}")
    
    def get_all_sap_customers(self):
        """Get all SAP customers for bulk analysis."""
        sap_customers = list(self.customers_collection.find({
            "customerType": "sap",
            "status": "active"
        }, {
            "CardCode": 1,
            "CardName": 1,
            "customerType": 1
        }))
        
        return sap_customers
    
    def get_customer_purchase_history(self, customer_id):
        """Get customer's recent purchase history from invoices."""
        # Get recent invoices for the customer
        recent_invoices = list(self.invoices_collection.find({
            "CardCode": customer_id
        }, {
            "DocumentLines": 1,
            "DocDate": 1,
            "DocTotal": 1
        }).sort("DocDate", -1).limit(10))
        
        # Extract items from recent purchases
        recent_items = []
        for invoice in recent_invoices:
            for line in invoice.get('DocumentLines', []):
                item_code = line.get('ItemCode')
                if item_code:
                    recent_items.append(item_code)
        
        return recent_items 