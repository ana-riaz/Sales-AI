# PQF - Product Recommendation System

A sophisticated web-based product recommendation system built with Python Flask, MongoDB, and JavaScript. The system analyzes customer purchase history and provides personalized product recommendations using multiple similarity algorithms.

## 🎯 How the Recommendation System Works

### Core Algorithm Overview

The recommendation system uses a **hybrid approach** combining:

1. **Purchase History Analysis** - Analyzes customer's past orders
2. **Similarity Matching** - Finds similar products using multiple criteria
3. **Inventory Integration** - Checks real-time stock availability
4. **Frequency Analysis** - Prioritizes frequently ordered items

### Data Flow Architecture

```
Customer Request → Flask API → MongoDB Query → Recommendation Engine → Response
     ↓                    ↓              ↓              ↓              ↓
  Customer ID    →   Order History  →  Item Details →  Similar Items →  JSON Response
```

### Step-by-Step Recommendation Process

#### 1. **Customer Order History Retrieval**
- Queries MongoDB for all invoices belonging to the customer
- Extracts item codes, quantities, dates, and prices
- Filters out items with zero quantities (returns/exchanges)
- Builds a comprehensive purchase profile

#### 2. **Frequency Analysis**
```python
def analyze_order_frequency(order_history):
    # Count total quantities per item
    # Sort by frequency and total quantity
    # Return top items for recommendation
```

#### 3. **Similarity Matching (Three Filters)**

**A. Name-Based Similarity**
- Uses regex pattern matching on item names
- Extracts key words and finds items with similar naming patterns
- Example: "Steel Pipe 2in" matches "Steel Pipe 3in"

**B. Code-Based Similarity**
- Analyzes item codes for structural patterns
- Groups items with similar code prefixes/suffixes
- Example: "PIPE-001" matches "PIPE-002"

**C. Subcategory Matching**
- Groups items by their subcategory classification
- Finds items in the same product category
- Provides broader category-based recommendations

#### 4. **Inventory Integration**
- Checks real-time stock levels for recommended items
- Marks items as "Available" or "Out of Stock"
- Includes stock quantities in recommendations

#### 5. **Recommendation Formatting**
- Combines purchase history with similar items
- Includes recent invoice details (last 3 purchases)
- Provides reasoning for each recommendation

### Technical Architecture

#### Backend Components

**`app.py`** - Flask Web Server
- RESTful API endpoints
- Customer data retrieval
- Response formatting and JSON export
- Error handling and logging

**`Recommend_items.py`** - Core Recommendation Engine
- `get_personalized_recommendations()` - Main recommendation function
- `get_customer_order_history()` - Purchase history analysis
- `find_similar_items_by_name()` - Name-based similarity
- `find_similar_items_by_code()` - Code-based similarity
- `analyze_order_frequency()` - Frequency analysis

**`setup_indexes.py`** - Database Optimization
- Creates MongoDB indexes for performance
- Optimizes queries for large datasets
- Ensures fast response times

#### Database Schema

**Customers Collection**
```json
{
  "CardCode": "C12345",
  "CardName": "Customer Name",
  "customerType": "sap",
  "address": {
    "city": "City",
    "country": "Country"
  },
  "phoneNumber": "123-456-7890"
}
```

**Invoices Collection**
```json
{
  "CardCode": "C12345",
  "DocNum": "INV001",
  "DocDate": "2024-01-15",
  "DocTotal": 1500.00,
  "DocumentLines": [
    {
      "ItemCode": "ITEM001",
      "ItemDescription": "Product Description",
      "Quantity": 10,
      "Price": 150.00,
      "LineTotal": 1500.00
    }
  ]
}
```

**Items Collection**
```json
{
  "ItemCode": "ITEM001",
  "ItemName": "Product Name",
  "ItemsGroupCode": 100,
  "U_SubCategory": "Pipes",
  "U_cat_lev_2": "Plumbing",
  "QuantityOnStock": 50,
  "ItemPrices": [...]
}
```

### API Endpoints

#### GET `/api/recommendations/<customer_id>`
Returns personalized recommendations for a customer.

**Response Format:**
```json
{
  "success": true,
  "customerInfo": {
    "name": "Customer Name",
    "cardCode": "C12345",
    "location": "City, Country",
    "phone": "123-456-7890",
    "type": "sap"
  },
  "recommendations": [
    {
      "itemCode": "ITEM001",
      "itemDescription": "Product Description",
      "totalQuantity": 25,
      "inStock": 50,
      "available": true,
      "reason": "Based on your order history",
      "invoices": [
        {
          "docNum": "INV001",
          "docDate": "2024-01-15",
          "quantity": 10,
          "price": 150.00
        }
      ],
      "similarItemsByName": [...],
      "similarItemsByCode": [...],
      "tag": "Based on purchase history"
    }
  ]
}
```

### Features

#### ✅ **Personalized Recommendations**
- Based on individual customer purchase history
- Considers order frequency and quantities
- Excludes previously purchased items from similar items

#### ✅ **Multi-Criteria Similarity**
- Name-based matching using regex patterns
- Code-based structural similarity
- Subcategory grouping for broader recommendations

#### ✅ **Real-Time Inventory**
- Live stock level checking
- Availability status for each recommendation
- Stock quantity information

#### ✅ **Purchase History Integration**
- Recent invoice details (last 3 purchases)
- Price and quantity history
- Order date tracking

#### ✅ **Performance Optimization**
- MongoDB indexes for fast queries
- Efficient data aggregation
- Cached item details

#### ✅ **Data Export**
- Automatic JSON export of analysis results
- Timestamped files with customer ID
- Error logging and debugging

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aena800/PQF.git
   cd PQF
   ```

2. **Install dependencies:**
   ```bash
   pip install flask flask-cors pymongo
   ```

3. **Set up database indexes:**
   ```bash
   python setup_indexes.py
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the web interface:**
   - Open browser to `http://localhost:5000`
   - Enter a customer ID to get recommendations

### Usage Examples

#### Command Line Interface
```bash
python Recommend_items.py
# Enter customer ID when prompted
# View detailed recommendation analysis
```

#### Web Interface
1. Navigate to the web application
2. Enter a customer ID (e.g., "C12345")
3. View personalized recommendations with similar items
4. Check stock availability and purchase history

#### API Usage
```bash
curl http://localhost:5000/api/recommendations/C12345
```

### Performance Considerations

- **Database Indexes**: Optimized for fast customer and item lookups
- **Query Efficiency**: Single queries for bulk data retrieval
- **Memory Management**: Processes items in batches
- **Caching**: Item details cached during recommendation generation

### Error Handling

- Customer not found: Returns 404 with appropriate message
- No order history: Returns empty recommendations with explanation
- Database errors: Logged and returned as JSON
- Invalid customer IDs: Validated before processing

