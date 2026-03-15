from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from features.personalized_recommendations.Recommend_items import get_personalized_recommendations, customers_col, invoices_col, items_col
from features.predictive_ordering.predictive_ordering import get_predictive_recommendations, get_all_sap_predictions
from features.upselling_cross_selling.upselling_engine import UpsellingEngine

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

def save_analysis_to_json(analysis_result, customer_id):
    """Save analysis results to a JSON file."""
    # Create results directory if it doesn't exist
    results_dir = "features/personalized_recommendations/analysis_results"
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
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/recommendations')
def recommendations_index():
    return render_template('personalized_recommendations.html')

@app.route('/predictive')
def predictive_index():
    return render_template('predictive_ordering.html')

@app.route('/upselling')
def upselling_index():
    return render_template('upselling_cross_selling.html')

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

# Predictive Ordering System Endpoints
@app.route('/api/predictive/<customer_id>')
def get_predictive_api(customer_id):
    """Get predictive ordering suggestions for a specific customer"""
    try:
        predictions = get_predictive_recommendations(customer_id)
        
        if not predictions:
            return jsonify({
                "success": False,
                "message": f"No predictions available for customer {customer_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "predictions": predictions
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route('/api/predictive/all-sap')
def get_all_sap_predictive_api():
    """Get predictive ordering suggestions for all SAP customers"""
    try:
        all_predictions = get_all_sap_predictions()
        
        return jsonify({
            "success": True,
            "total_customers": len(all_predictions),
            "predictions": all_predictions
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500

# Feature4: Upselling and Cross-Selling Endpoints
@app.route('/api/upselling/recommendations/<customer_id>', methods=['GET'])
def get_upselling_recommendations(customer_id):
    """Generate customer-specific upselling and cross-selling recommendations"""
    try:
        # Initialize upselling engine
        upselling_engine = UpsellingEngine(
            connection_string=os.getenv('MONGODB_CONNECTION_STRING'),
            database_name=os.getenv('MONGODB_DATABASE')
        )
        
        # Generate recommendations for the customer
        recommendations = upselling_engine.generate_recommendations(customer_id)
        
        return jsonify({
            "success": True,
            "customer_info": recommendations['customer_info'],
            "bundle_suggestions": recommendations['bundle_suggestions'],
            "complementary_items": recommendations['complementary_items'],
            "popular_addons": recommendations['popular_addons'],
            "customer_specific_suggestions": recommendations['customer_specific_suggestions'],
            "analysis_summary": recommendations['analysis_summary']
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500



@app.route('/api/upselling/customer-history/<customer_id>')
def get_customer_history(customer_id):
    """Get customer's recent purchase history"""
    try:
        # Initialize upselling engine
        upselling_engine = UpsellingEngine(
            connection_string=os.getenv('MONGODB_CONNECTION_STRING'),
            database_name=os.getenv('MONGODB_DATABASE')
        )
        
        # Get customer purchase history
        recent_items = upselling_engine.get_customer_purchase_history(customer_id)
        
        return jsonify({
            "success": True,
            "customer_id": customer_id,
            "items": recent_items
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 