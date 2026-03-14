// Global variables
let currentCustomerId = '';
let currentRecommendations = [];

// Demo sample response (used when demo mode is enabled)
function getDemoRecommendations(customerId) {
    return new Promise(resolve => {
        setTimeout(() => {
            resolve({
                success: true,
                customerInfo: {
                    name: 'Demo Customer',
                    cardCode: customerId || 'C0000',
                    location: 'Demo City, Demo Country',
                    phone: '+123 456 7890',
                    type: 'sap'
                },
                recommendations: [
                    {
                        itemCode: 'ITEM-001',
                        itemDescription: 'Demo Product Alpha',
                        totalQuantity: 42,
                        inStock: 12,
                        available: true,
                        reason: 'Frequently ordered together with past purchases.',
                        invoices: [
                            { DocNum: 1001, DocDate: '2026-03-10', Quantity: 10, Price: 12.5 },
                            { DocNum: 1002, DocDate: '2026-03-03', Quantity: 8, Price: 12.5 }
                        ],
                        similarItemsByName: [
                            { ItemCode: 'ITEM-002', ItemName: 'Demo Product Beta', QuantityOnStock: 8, Tag: 'Suggested' },
                            { ItemCode: 'ITEM-003', ItemName: 'Demo Product Gamma', QuantityOnStock: 4, Tag: 'Suggested' }
                        ],
                        similarItemsByCode: [
                            { ItemCode: 'ITEM-004', ItemName: 'Demo Product Delta', QuantityOnStock: 18, Tag: 'Similar Category' }
                        ],
                        tag: 'Based on purchase history'
                    },
                    {
                        itemCode: 'ITEM-010',
                        itemDescription: 'Demo Product Omega',
                        totalQuantity: 18,
                        inStock: 0,
                        available: false,
                        reason: 'Recently ordered but currently out of stock.',
                        invoices: [
                            { DocNum: 1020, DocDate: '2026-02-26', Quantity: 5, Price: 18.0 }
                        ],
                        similarItemsByName: [],
                        similarItemsByCode: [],
                        tag: 'Out of stock suggestion'
                    }
                ]
            });
        }, 600);
    });
}

// Main function to get recommendations
async function getRecommendations() {
    const customerId = document.getElementById('customerId').value.trim();
    const demoMode = document.getElementById('demoMode')?.checked;

    if (!customerId && !demoMode) {
        showError('Please enter a Customer ID');
        return;
    }

    currentCustomerId = customerId || 'DEMO';
    showLoading();
    hideError();
    hideCustomerInfo();
    hideRecommendations();

    try {
        let data;
        if (demoMode) {
            data = await getDemoRecommendations(currentCustomerId);
        } else {
            // Call the real API endpoint
            const response = await fetch(`/api/recommendations/${encodeURIComponent(customerId)}`);
            data = await response.json();
        }

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
    document.getElementById('filterSection').classList.add('hidden');
}

// Display recommendations
function displayRecommendations(recommendations) {
    currentRecommendations = recommendations;
    const container = document.getElementById('recommendationsList');
    container.innerHTML = '';
    
    recommendations.forEach((rec, index) => {
        const recElement = createRecommendationElement(rec, index + 1);
        container.appendChild(recElement);
    });
    
    document.getElementById('recommendations').classList.remove('hidden');
    document.getElementById('filterSection').classList.remove('hidden');
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
            <div class="similar-items-name" data-filter="name">
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
            </div>
            <h4>Similar Items By Category</h4>
            <div class="similar-items-code" data-filter="category">
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
        </div>
        
        <div class="reason">
            <strong>Why Recommended:</strong> ${rec.reason}
        </div>
    `;
    
    return div;
}

// Filter recommendations based on selected filter type
function filterRecommendations() {
    const filterType = document.getElementById('filterType').value;
    const similarItemsName = document.querySelectorAll('.similar-items-name');
    const similarItemsCode = document.querySelectorAll('.similar-items-code');
    
    similarItemsName.forEach(container => {
        if (filterType === 'all' || filterType === 'name') {
            container.style.display = 'block';
        } else {
            container.style.display = 'none';
        }
    });
    
    similarItemsCode.forEach(container => {
        if (filterType === 'all' || filterType === 'category') {
            container.style.display = 'block';
        } else {
            container.style.display = 'none';
        }
    });
    
    // Update section headers visibility
    const nameHeaders = document.querySelectorAll('.similar-items h4:first-of-type');
    const codeHeaders = document.querySelectorAll('.similar-items h4:last-of-type');
    
    nameHeaders.forEach(header => {
        if (filterType === 'all' || filterType === 'name') {
            header.style.display = 'block';
        } else {
            header.style.display = 'none';
        }
    });
    
    codeHeaders.forEach(header => {
        if (filterType === 'all' || filterType === 'category') {
            header.style.display = 'block';
        } else {
            header.style.display = 'none';
        }
    });
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