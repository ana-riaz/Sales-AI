from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import os
from Recommend_items import get_personalized_recommendations, customers_col, invoices_col, items_col

app = Flask(__name__)
CORS(app)

def save_analysis_to_json(analysis_result, customer_id):
    """Save analysis results to a JSON file."""
    # Create results directory if it doesn't exist
    results_dir = "analysis_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Create filename with timestamp and customer ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{results_dir}/analysis_{customer_id}_{timestamp}.json"
    
    # Save to JSON file with proper formatting
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Analysis results saved to: {filename}")
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recommendations/<customer_id>')
def get_recommendations_api(customer_id):
    try:
        # Get customer information
        customer_info = customers_col.find_one({"CardCode": customer_id})
        
        if not customer_info:
            return jsonify({
                "success": False,
                "message": f"Customer {customer_id} not found"
            }), 404
        
        # Get recommendations using your existing function
        recommendations_data = get_personalized_recommendations(customer_id, invoices_col, items_col)
        
        if not recommendations_data['recommendations']:
            return jsonify({
                "success": False,
                "message": recommendations_data['message']
            }), 404
        
        # Format customer info
        customer_data = {
            "name": customer_info.get('CardName', 'Unknown'),
            "cardCode": customer_info.get('CardCode', ''),
            "location": f"{customer_info.get('address', {}).get('city', 'Unknown')}, {customer_info.get('address', {}).get('country', 'Unknown')}",
            "phone": customer_info.get('phoneNumber', 'Not provided'),
            "type": customer_info.get('customerType', 'Unknown')
        }
        
        # Format recommendations for frontend
        formatted_recommendations = []
        for rec in recommendations_data['recommendations']:
            # Format invoices
            formatted_invoices = []
            for inv in rec.get('Invoices', [])[:3]:  # Limit to 3 most recent
                if inv.get('DocDate'):
                    date_str = inv['DocDate'].strftime('%Y-%m-%d') if hasattr(inv['DocDate'], 'strftime') else str(inv['DocDate'])
                else:
                    date_str = 'Unknown'
                
                formatted_invoices.append({
                    "docNum": inv.get('DocNum', ''),
                    "docDate": date_str,
                    "quantity": inv.get('Quantity', 0),
                    "price": inv.get('Price', 0)
                })
            
            # Format similar items for all three filters
            def format_similar_list(sim_list):
                return [{
                    "itemCode": sim.get('ItemCode', ''),
                    "itemName": sim.get('ItemName', ''),
                    "inStock": sim.get('QuantityOnStock', 0),
                    "tag": sim.get('Tag', '')
                } for sim in sim_list]
            
            formatted_recommendations.append({
                "itemCode": rec.get('ItemCode', ''),
                "itemDescription": rec.get('ItemDescription', ''),
                "totalQuantity": rec.get('TotalQuantity', 0),
                "inStock": rec.get('InStock', 0),
                "available": rec.get('Available', False),
                "reason": rec.get('reason', 'Based on your order history'),
                "invoices": formatted_invoices,
                "similarItemsByName": format_similar_list(rec.get('SimilarItemsByName', [])),
                "similarItemsByCode": format_similar_list(rec.get('SimilarItemsByCode', [])),
                "tag": rec.get('Tag', 'Based on purchase history')
            })
        
        # Create the complete analysis result
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "customerId": customer_id,
            "success": True,
            "customerInfo": customer_data,
            "recommendations": formatted_recommendations,
            "analysisMetadata": {
                "totalRecommendations": len(formatted_recommendations),
                "analysisDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "filteredZeroQuantities": True,
                "similaritySearchesEnabled": True
            }
        }
        
        # Save to JSON file
        save_analysis_to_json(analysis_result, customer_id)
        
        return jsonify({
            "success": True,
            "customerInfo": customer_data,
            "recommendations": formatted_recommendations
        })
        
    except Exception as e:
        # Save error result to JSON file
        error_result = {
            "timestamp": datetime.now().isoformat(),
            "customerId": customer_id,
            "success": False,
            "error": str(e),
            "analysisMetadata": {
                "analysisDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "errorOccurred": True
            }
        }
        save_analysis_to_json(error_result, customer_id)
        
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 