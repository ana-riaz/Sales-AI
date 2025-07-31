# AI Sales Module - Halal Food Deliveries

A comprehensive AI-powered sales module built with Python Flask, MongoDB, and JavaScript. The system provides both personalized product recommendations (Feature2) and predictive ordering suggestions (Feature3) for SAP customers in the halal food delivery industry.

## System Overview

Main AI features designed to enhance customer experience and drive sales:

### **Feature: Personalized Product Recommendation System**

1. **Purchase History Analysis** - Analyzes customer's past orders
2. **Similarity Matching** - Finds similar products using multiple criteria
3. **Inventory Integration** - Checks real-time stock availability
4. **Frequency Analysis** - Prioritizes frequently ordered items

### **Step-by-Step Recommendation Process**

#### 1. **Customer Order History Retrieval**
- Queries MongoDB for all invoices belonging to the customer
- Extracts item codes, quantities, dates, and prices
- Filters out items with zero quantities (returns/exchanges)
- Builds a comprehensive purchase profile

#### 2. **Similarity Matching (Two Filters)**

**A. Name-Based Similarity**
- Uses regex pattern matching on item names
- Extracts key words and finds items with similar naming patterns

**B. Category-Based Similarity**
- Uses ItemsGroupCode from the database
- Groups items in the same product category

### **API Endpoints**

#### **GET `/api/recommendations/<customer_id>`**
Returns personalized recommendations for a customer.


---

### **Feature: Predictive Ordering System**

The Predictive Ordering System analyzes customer purchase patterns to predict when they should reorder items, providing intelligent suggestions like:
- "Add your usual [ItemName]" - when customer is overdue for reorder based on historical patterns
- "Stock running low on [ItemName]?" - when inventory is running low on a certain item

### **Target Customers**
- **SAP Customers Only**: Customers with CardCode starting with 'C'
- **Pattern-Based**: Only customers with consistent ordering patterns (weekly to monthly intervals)
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


### **API Endpoints**

#### **GET `/api/predictive/<customer_id>`**
Returns predictive ordering suggestions for a specific customer.

#### **GET `/api/predictive/all-sap`**
Returns predictive suggestions for all SAP customers (limited to first 10 for performance).


**CSV Columns:**
```
Customer ID, Customer Name, Customer Type, Country, Item Code, Item Name,
Average Interval (days), Average Quantity (units), Average Price, Current Stock,
Total Orders, Last Order Date
```

---

### **Data Storage**
- **Analysis Results**: Saved to `Feature2/analysis_results/` directory
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

### **3. Configure MongoDB Connection**
Update the connection string in `Feature3/predictive_ordering.py`:
```python
MONGODB_CONNECTION_STRING = "your_mongodb_connection_string"
MONGODB_DATABASE = "your_database_name"
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
- **Feature2 (Recommendations)**: `http://localhost:5000`
- **Feature3 (Predictive)**: `http://localhost:5000/predictive`

---

## 📊 Usage Examples

### **Feature3: Predictive Ordering System**

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

### **Feature2: Recommendation System**

#### **Web Interface**
1. Navigate to `http://localhost:5000`
2. Enter a customer ID
3. View personalized recommendations with similar items

#### **API Usage**
```bash
curl http://localhost:5000/api/recommendations/C12345
```

---


