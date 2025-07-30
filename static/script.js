// Global variables
let currentCustomerId = '';

// Main function to get recommendations
async function getRecommendations() {
    const customerId = document.getElementById('customerId').value.trim();
    
    if (!customerId) {
        showError('Please enter a Customer ID');
        return;
    }
    
    currentCustomerId = customerId;
    showLoading();
    hideError();
    hideCustomerInfo();
    hideRecommendations();
    
    try {
        // Call the real API endpoint
        const response = await fetch(`/api/recommendations/${encodeURIComponent(customerId)}`);
        const data = await response.json();
        if (data.success) {
            displayCustomerInfo(data.customerInfo);
            displayRecommendations(data.recommendations);
        } else {
            showError(data.message || 'No recommendations found.');
        }
    } catch (error) {
        showError('An error occurred while fetching recommendations');
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
}

// Display customer information
function displayCustomerInfo(customerInfo) {
    document.getElementById('customerName').textContent = customerInfo.name;
    document.getElementById('customerCode').textContent = customerInfo.cardCode;
    document.getElementById('customerLocation').textContent = customerInfo.location;
    document.getElementById('customerPhone').textContent = customerInfo.phone;
    document.getElementById('customerType').textContent = customerInfo.type;
    
    document.getElementById('customerInfo').classList.remove('hidden');
}

function hideCustomerInfo() {
    document.getElementById('customerInfo').classList.add('hidden');
}

function hideRecommendations() {
    document.getElementById('recommendations').classList.add('hidden');
}

// Display recommendations
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendationsList');
    container.innerHTML = '';
    
    recommendations.forEach((rec, index) => {
        const recElement = createRecommendationElement(rec, index + 1);
        container.appendChild(recElement);
    });
    
    document.getElementById('recommendations').classList.remove('hidden');
}

// Create recommendation element
function createRecommendationElement(rec, index) {
    const div = document.createElement('div');
    div.className = `recommendation-item ${!rec.available ? 'out-of-stock' : ''}`;
    
    div.innerHTML = `
        <div class="recommendation-header">
            <div class="product-title">${index}. ${rec.itemDescription}</div>
            <div class="product-code">${rec.itemCode}</div>
            <div class="recommendation-tag">${rec.tag || ''}</div>
        </div>
        
        <div class="product-stats">
            <div class="stat-item">
                <div class="stat-value">${rec.totalQuantity}</div>
                <div class="stat-label">Total Ordered</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${rec.inStock}</div>
                <div class="stat-label">In Stock</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${rec.available ? 'Available' : 'Out of Stock'}</div>
                <div class="stat-label">Status</div>
            </div>
        </div>
        
        <div class="purchase-history">
            <h4>Purchase History</h4>
            ${rec.invoices.map(inv => `
                <div class="purchase-item">
                    Invoice #${inv.docNum} (${inv.docDate}): ${inv.quantity} units @ €${inv.price.toFixed(2)}
                </div>
            `).join('')}
        </div>
        
        <div class="similar-items">
            <h4>Similar Items By Name</h4>
            ${rec.similarItemsByName && rec.similarItemsByName.length > 0 ? rec.similarItemsByName.map(item => `
                <div class="similar-item">
                    <div>
                        <div class="similar-item-name">${item.itemName}</div>
                        <div class="similar-item-code">${item.itemCode}</div>
                        <div class="similar-item-tag">${item.tag || ''}</div>
                    </div>
                    <span class="stock-status ${item.inStock > 0 ? 'in-stock' : 'out-of-stock'}">
                        ${item.inStock > 0 ? 'In Stock' : 'Out of Stock'}
                    </span>
                </div>
            `).join('') : '<div class="no-similar">No similar items found by name.</div>'}
            <h4>Similar Items By Code</h4>
            ${rec.similarItemsByCode && rec.similarItemsByCode.length > 0 ? rec.similarItemsByCode.map(item => `
                <div class="similar-item">
                    <div>
                        <div class="similar-item-name">${item.itemName}</div>
                        <div class="similar-item-code">${item.itemCode}</div>
                        <div class="similar-item-tag">${item.tag || ''}</div>
                    </div>
                    <span class="stock-status ${item.inStock > 0 ? 'in-stock' : 'out-of-stock'}">
                        ${item.inStock > 0 ? 'In Stock' : 'Out of Stock'}
                    </span>
                </div>
            `).join('') : '<div class="no-similar">No similar items found by code.</div>'}

        </div>
        
        <div class="reason">
            <strong>Why Recommended:</strong> ${rec.reason}
        </div>
    `;
    
    return div;
}

// UI Helper functions
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('error').classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Allow Enter key to trigger search
    document.getElementById('customerId').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            getRecommendations();
        }
    });
}); 