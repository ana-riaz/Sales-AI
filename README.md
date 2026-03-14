# AI Sales Intelligence Platform

A comprehensive AI-powered sales intelligence platform built with Python Flask, MongoDB, and JavaScript. The system provides personalized product recommendations, predictive ordering suggestions, and AI-driven upselling and cross-selling for SAP customers in the halal food delivery industry.

## System Overview

Main AI features designed to enhance customer experience and drive sales:

### **Personalized Product Recommendations**

1. **Purchase History Analysis** - Analyzes customer's past orders
2. **Similarity Matching** - Finds similar products using multiple criteria
3. **Inventory Integration** - Checks real-time stock availability
4. **Frequency Analysis** - Prioritizes frequently ordered items

### **Predictive Ordering System**

The Predictive Ordering System analyzes customer purchase patterns to predict when they should reorder items, providing intelligent suggestions like:
- "Add your usual [ItemName]" - when customer is overdue for reorder based on historical patterns
- "Stock running low on [ItemName]?" - when inventory is running low on a certain item

### **AI-Driven Upselling and Cross-Selling**

The AI-Driven Upselling and Cross-Selling System analyzes deal patterns to provide intelligent product recommendations that increase average order value and customer satisfaction.
- **Recent Activity**: Focuses on customers with orders in the last 1 year (365 days)

### **Algorithm Architecture**


**Pattern Analysis Process:**
- **Data Collection**: Fetches all invoices for the customer from last 1 year
- **Grouping**: Groups orders by ItemCode to analyze each item separately
- **Interval Calculation**: Computes days between consecutive orders
- **Statistical Analysis**: Calculates mean, median, min, and max intervals (rounded values)
- **Pattern Validation**: Ensures patterns are within reasonable ranges (7-90 days)


**Interval Analysis:**
- **Weekly Patterns**: 7-14 days between orders
- **Bi-weekly Patterns**: 14-21 days between orders  
- **Monthly Patterns**: 21-90 days between orders
- **Excluded Patterns**: Less than 7 days or more than 90 days



**Inventory Analysis:**
- **Stock Levels**: Current quantity on hand
- **Stock Thresholds**: Based on customer's average order quantity (2x threshold)
- **Low Stock Alerts**: When stock is below 2x average order quantity
- **Item Validity**: Only suggest items with `Valid: 'tYES'` (exclude `Valid: 'tNO'`)


**Suggestion Types:**

**A. Usual Reorder Suggestions**
```python
if days_since_last_order >= avg_interval + 3 and days_since_last_order <= avg_interval + 10:
    # Generate "Add your usual [ItemName]" suggestion
```
- **Trigger**: Customer is 3-10 days overdue for reorder based on historical pattern
- **Priority**: High if overdue by more than 8 days, Medium otherwise
- **Minimum Items**: At least 3 items per category for consistent display

**B. Low Stock Alerts**
```python
if current_stock < stock_threshold and days_since_last_order <= 90:
    # Generate "Stock running low on [ItemName]?" suggestion
```
- **Trigger**: Current stock is below 2x customer's average order quantity
- **Priority**: High if stock is below average order quantity, Medium otherwise
- **Negative Stock**: Items with negative stock marked as "Available on Request"
- **Minimum Items**: At least 3 items per category for consistent display
- **Rounded Values**: Clean integer display for days, decimal display for quantities

### **Filtering Criteria**

#### **Temporal Filters**
- **Recent Activity**: Only items ordered in the last 1 year (365 days)
- **Reasonable Intervals**: Only patterns between 7-90 days
- **Overdue Limits**: Suggestions only for items overdue by 3-10 days

#### **Pattern Quality Filters**
- **Minimum Orders**: At least 2 orders required to calculate patterns
- **Consistent Patterns**: Focus on customers with regular ordering habits
- **Relevant Suggestions**: Only generate suggestions for actionable patterns
- **Item Validity**: Only include items with `Valid: 'tYES'` status


**CSV Columns:**
```
Customer ID, Customer Name, Customer Type, Country, Item Code, Item Name,
Average Interval (days), Average Quantity (units), Average Price, Current Stock,
Total Orders, Last Order Date
```

---

### **Feature: AI-Driven Upselling and Cross-Selling System**

The AI-Driven Upselling and Cross-Selling System analyzes deal patterns to provide intelligent product recommendations that increase average order value and customer satisfaction.

### **Target Customers**
- **SAP Customers Only**: Customers with `customerType: "sap"`
- **Valid Products Only**: Items with `Valid: "tYES"` status
- **Deal-Based Analysis**: Focuses on actual deal combinations and purchase patterns

### **Algorithm Architecture**

**Bundle Analysis Process:**
- **Deal Collection**: Analyzes all deals with multiple products
- **Pattern Recognition**: Identifies items frequently purchased together
- **Frequency Analysis**: Calculates how often items appear in bundles
- **Complementary Mapping**: Maps items that are frequently bought together

**Recommendation Types:**

**A. Bundle Completion Suggestions**
```python
if customer_items_set.intersection(bundle_items_set):
    missing_items = bundle_items_set - customer_items_set
    # Generate "Complete your bundle!" suggestions
```
- **Trigger**: Customer's items are part of a popular bundle
- **Message**: "Complete your bundle! Other customers buy these X items together"
- **Priority**: Based on bundle frequency (minimum 2 occurrences)

**B. Complementary Item Suggestions**
```python
if item_code in complementary_items and frequency >= 2:
    # Generate "Frequently bought with [ItemCode]" suggestions
```
- **Trigger**: Items frequently purchased with customer's current items
- **Message**: "Frequently bought with [ItemCode]"
- **Priority**: Based on co-purchase frequency

**C. Popular Add-on Suggestions**
```python
if item_code in top_items and frequency >= 3:
    # Generate "Popular item - bought X times" suggestions
```
- **Trigger**: High-frequency items not in customer's current selection
- **Message**: "Popular item - bought X times"
- **Priority**: Based on overall purchase frequency

### **Filtering Criteria**

#### **Product Filters**
- **Valid Items Only**: Only items with `Valid: "tYES"` status
- **Stock Availability**: Shows current stock levels for each recommendation
- **Price Information**: Displays default pricing from PriceList 1

#### **Bundle Quality Filters**
- **Minimum Frequency**: Bundles must appear at least 2 times in deals
- **Multiple Items**: Only analyzes deals with 2+ products
- **Unique Patterns**: Removes duplicate recommendations

### **API Endpoints**

#### **GET `/api/upselling/recommendations/<customer_id>`**
Generates customer-specific upselling and cross-selling recommendations based on their purchase history.

**Response:**
```json
{
  "success": true,
  "customer_info": {
    "card_code": "C12345",
    "card_name": "Customer Name",
    "customer_type": "sap",
    "location": "City, Country"
  },
  "bundle_suggestions": [...],
  "complementary_items": [...],
  "popular_addons": [...],
  "customer_specific_suggestions": [...],
  "analysis_summary": {...}
}
```



#### **GET `/api/upselling/customer-history/<customer_id>`**
Returns customer's recent purchase history from invoices.

**Response:**
```json
{
  "success": true,
  "customer_id": "C12345",
  "items": ["item1", "item2", "item3"]
}
```

---

### **Data Storage**
- **Analysis Results**: Saved to `features/personalized_recommendations/analysis_results/` directory
- **File Naming**: `analysis_{customer_id}_{timestamp}.json`
- **Format**: Comprehensive JSON with all recommendation data

---

## 🚀 Setup Instructions

### **1. Clone the Repository**
   ```bash
git clone https://github.com/aena800/AI-Sales-Module.git
cd AI-Sales-Module
   ```

### **2. Install Dependencies**
   ```bash
   pip install flask flask-cors pymongo
   ```

### **3. Configure Environment Variables**
Create a `.env` file in the root directory with your MongoDB credentials:
```env
MONGODB_CONNECTION_STRING=your_mongodb_connection_string
MONGODB_DATABASE=your_database_name
```

### **4. Set up Database Indexes**
   ```bash
   python setup_indexes.py
   ```

### **5. Run the Application**
   ```bash
   python app.py
   ```

### **6. Access the Web Interface**
- **Personalized Recommendations**: `http://localhost:5000`
- **Predictive Ordering**: `http://localhost:5000/predictive`
- **Upselling & Cross-Selling**: `http://localhost:5000/upselling`

---

## 📊 Usage Examples

### **Feature4: AI-Driven Upselling and Cross-Selling**

#### **Web Interface**
1. Navigate to `http://localhost:5000/upselling`
2. Enter a SAP customer ID (e.g., C12345)
3. View bundle suggestions, complementary items, and popular add-ons
4. Analyze recommendation statistics and export results

#### **API Usage**
```bash
# Generate customer-specific recommendations
curl http://localhost:5000/api/upselling/recommendations/C12345

# Get customer purchase history
curl http://localhost:5000/api/upselling/customer-history/C12345
```

### **Predictive Ordering System**

#### **Web Interface**
1. Navigate to `http://localhost:5000/predictive`
2. Enter a SAP customer ID (e.g., "C12345")
3. View smart cart suggestions organized by category
4. Analyze order patterns in the table format
5. Export pattern data to CSV

#### **API Usage**
```bash
# Get predictions for specific customer
curl http://localhost:5000/api/predictive/C12345

# Get predictions for all SAP customers
curl http://localhost:5000/api/predictive/all-sap
```

### **Personalized Product Recommendations**

#### **Web Interface**
1. Navigate to `http://localhost:5000`
2. Enter a customer ID
3. View personalized recommendations with similar items

#### **API Usage**
```bash
curl http://localhost:5000/api/recommendations/C12345
```

---


=======
>>>>>>> 9ffa5c0f4cd4d9288066798b5559cda0841465c9
