// Feature4: AI-Driven Upselling and Cross-Selling JavaScript

let currentResults = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Feature4: AI-Driven Upselling and Cross-Selling loaded');
    
    // Add enter key support for inputs
    document.getElementById('customerId').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            generateCustomerRecommendations();
        }
    });
});

// Demo mode mock data
function getDemoUpsellingData() {
    return {
        success: true,
        customer_info: {
            card_code: 'C0001',
            card_name: 'Michael Chen',
            customer_type: 'sap',
            location: 'San Francisco, CA'
        },
        bundle_suggestions: [
            {
                message: 'Complete your healthy breakfast bundle — customers also buy these items together',
                bundle_frequency: 21,
                total_bundle_items: 4,
                missing_items: [
                    { item_code: 'BEV-1001', name: 'Greek Yogurt 500g', price: 4.99, stock: 12, customer_has: false },
                    { item_code: 'BEV-1002', name: 'Orange Juice 1L', price: 3.49, stock: 3, customer_has: false }
                ],
                complete_deal_items: [
                    { item_code: 'FOOD-0001', name: 'Organic Oats 500g', price: 5.99, stock: 4, customer_has: true },
                    { item_code: 'FOOD-0002', name: 'Mixed Berries 250g', price: 6.99, stock: 8, customer_has: true }
                ]
            }
        ],
        complementary_items: [
            { item_code: 'SNACK-2001', name: 'Trail Mix 200g', price: 7.99, stock: 15, frequency: 27 },
            { item_code: 'SNACK-2002', name: 'Dark Chocolate 100g', price: 4.50, stock: 5, frequency: 9 }
        ],
        popular_addons: [
            { item_code: 'BEV-3001', name: 'Green Tea Bags 20ct', price: 3.99, stock: 20, frequency: 35 }
        ],
        customer_specific_suggestions: [
            { message: 'Customers like you also buy this when ordering organic produce.', item_code: 'FOOD-4001', name: 'Avocado Oil 250ml', price: 12.99, stock: 6 }
        ],
        analysis_summary: {
            total_bundle_suggestions: 1,
            total_complementary_items: 2,
            total_popular_addons: 1,
            total_customer_suggestions: 1
        }
    };
}

// Generate customer-specific recommendations
async function generateCustomerRecommendations() {
    const customerId = document.getElementById('customerId').value.trim();
    const demoMode = document.getElementById('demoModeUpselling')?.checked;

    if (!customerId && !demoMode) {
        showAlert('Please enter a customer ID', 'warning');
        return;
    }

    showLoading(true);
    hideResults();

    try {
        let data;
        if (demoMode) {
            data = getDemoUpsellingData();
        } else {
            const response = await fetch(`/api/upselling/recommendations/${customerId}`);
            data = await response.json();
        }

        if (data.success) {
            currentResults = data;
            displayResults(data);
        } else {
            showAlert(data.message || 'Failed to generate recommendations', 'error');
        }
    } catch (error) {
        console.error('Error generating recommendations:', error);
        showAlert('Error connecting to server', 'error');
    } finally {
        showLoading(false);
    }
}



// Display results
function displayResults(data) {
    const totalRecommendations = (data.bundle_suggestions?.length || 0) + 
                                (data.complementary_items?.length || 0) + 
                                (data.popular_addons?.length || 0) +
                                (data.customer_specific_suggestions?.length || 0);
    
    if (totalRecommendations === 0) {
        showNoResults();
        return;
    }
    
    // Display customer info if available
    if (data.customer_info) {
        displayCustomerInfo(data.customer_info);
    }
    
    // Display bundle suggestions
    displayBundleSuggestions(data.bundle_suggestions || []);
    
    // Display complementary items
    displayComplementaryItems(data.complementary_items || []);
    
    // Display popular add-ons
    displayPopularAddons(data.popular_addons || []);
    
    // Display customer-specific suggestions
    displayCustomerSpecificSuggestions(data.customer_specific_suggestions || []);
    
    // Update statistics
    updateStatistics(data.analysis_summary || {});
    
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('noResults').style.display = 'none';
}

// Display bundle suggestions
function displayBundleSuggestions(suggestions) {
    const container = document.getElementById('bundleCards');
    
    if (suggestions.length === 0) {
        container.innerHTML = '<p class="text-muted">No bundle suggestions found</p>';
        return;
    }
    
    let html = '';
    
    suggestions.forEach(suggestion => {
        html += `
            <div class="recommendation-card bundle-suggestion">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h6 class="mb-1">
                            <i class="fas fa-boxes me-2 text-success"></i>
                            ${suggestion.message}
                        </h6>
                        <p class="text-muted mb-0">
                            Deal package frequency: <span class="badge bg-success">${suggestion.bundle_frequency} times</span>
                        </p>
                    </div>
                    <span class="frequency-badge">${suggestion.total_bundle_items} items</span>
                </div>
                
                <div class="mb-3">
                    <h6 class="text-success mb-2">
                        <i class="fas fa-check-circle me-1"></i>
                        Complete Deal Package:
                    </h6>
                    <div class="row">
                        ${suggestion.complete_deal_items ? suggestion.complete_deal_items.map(item => `
                            <div class="col-md-6 mb-2">
                                <div class="item-badge d-flex justify-content-between align-items-center ${item.customer_has ? 'border-success bg-light' : 'border-warning'}">
                                    <div>
                                        <div class="d-flex align-items-center">
                                            ${item.customer_has ? 
                                                '<i class="fas fa-check-circle text-success me-2" title="You have this item"></i>' : 
                                                '<i class="fas fa-plus-circle text-warning me-2" title="Add this item"></i>'
                                            }
                                            <div>
                                                <strong>${item.item_code}</strong>
                                                <br>
                                                <small class="text-muted">${item.name}</small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="text-end">
                                        <span class="price-tag">€${item.price.toFixed(2)}</span>
                                        <br>
                                        <span class="stock-indicator ${getStockClass(item.stock)}">
                                            ${getStockText(item.stock)}
                                        </span>
                                        ${item.customer_has ? 
                                            '<br><small class="text-success"><i class="fas fa-check"></i> You have this</small>' : 
                                            '<br><small class="text-warning"><i class="fas fa-plus"></i> Add to complete</small>'
                                        }
                                    </div>
                                </div>
                            </div>
                        `).join('') : suggestion.missing_items.map(item => `
                            <div class="col-md-6 mb-2">
                                <div class="item-badge d-flex justify-content-between align-items-center border-warning">
                                    <div>
                                        <div class="d-flex align-items-center">
                                            <i class="fas fa-plus-circle text-warning me-2" title="Add this item"></i>
                                            <div>
                                                <strong>${item.item_code}</strong>
                                                <br>
                                                <small class="text-muted">${item.name}</small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="text-end">
                                        <span class="price-tag">€${item.price.toFixed(2)}</span>
                                        <br>
                                        <span class="stock-indicator ${getStockClass(item.stock)}">
                                            ${getStockText(item.stock)}
                                        </span>
                                        <br><small class="text-warning"><i class="fas fa-plus"></i> Add to complete</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center">
                    <div class="text-muted">
                        <small>
                            <i class="fas fa-info-circle me-1"></i>
                            Complete the deal package to get the full bundle value
                        </small>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-success">${suggestion.total_bundle_items - suggestion.missing_items.length}/${suggestion.total_bundle_items} items</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Display complementary items
function displayComplementaryItems(items) {
    const container = document.getElementById('complementaryCards');
    
    if (items.length === 0) {
        container.innerHTML = '<p class="text-muted">No complementary items found</p>';
        return;
    }
    
    let html = '';
    
    items.forEach(item => {
        html += `
            <div class="recommendation-card complementary-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <i class="fas fa-link me-2 text-primary"></i>
                            ${item.message}
                        </h6>
                        <p class="mb-2">
                            <strong>${item.item_code}</strong> - ${item.name}
                        </p>
                        <div class="d-flex gap-2 align-items-center">
                            <span class="price-tag">€${item.price.toFixed(2)}</span>
                            <span class="stock-indicator ${getStockClass(item.stock)}">
                                ${getStockText(item.stock)}
                            </span>
                            <span class="frequency-badge">
                                In ${item.frequency} deal packages
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Display popular add-ons
function displayPopularAddons(items) {
    const container = document.getElementById('popularCards');
    
    if (items.length === 0) {
        container.innerHTML = '<p class="text-muted">No popular add-ons found</p>';
        return;
    }
    
    let html = '';
    
    items.forEach(item => {
        html += `
            <div class="recommendation-card popular-addon">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <i class="fas fa-star me-2 text-warning"></i>
                            ${item.message}
                        </h6>
                        <p class="mb-2">
                            <strong>${item.item_code}</strong> - ${item.name}
                        </p>
                        <div class="d-flex gap-2 align-items-center">
                            <span class="price-tag">€${item.price.toFixed(2)}</span>
                            <span class="stock-indicator ${getStockClass(item.stock)}">
                                ${getStockText(item.stock)}
                            </span>
                            <span class="frequency-badge">
                                ${item.frequency} deal packages
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Display customer information
function displayCustomerInfo(customerInfo) {
    // Add customer info to the page header or create a new section
    const header = document.querySelector('.bg-primary h1');
    if (header) {
        header.innerHTML = `
            <i class="fas fa-chart-line me-2"></i>
            AI-Driven Upselling & Cross-Selling
            <small class="d-block mt-1 opacity-75">${customerInfo.card_name} (${customerInfo.card_code})</small>
        `;
    }
}

// Display customer-specific suggestions
function displayCustomerSpecificSuggestions(suggestions) {
    const container = document.getElementById('customerSpecificCards');
    
    if (suggestions.length === 0) {
        container.innerHTML = '<p class="text-muted">No personalized suggestions found</p>';
        return;
    }
    
    let html = '';
    
    suggestions.forEach(suggestion => {
        html += `
            <div class="recommendation-card customer-specific">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <i class="fas fa-user-check me-2 text-info"></i>
                            ${suggestion.message}
                        </h6>
                        <p class="mb-2">
                            <strong>${suggestion.item_code}</strong> - ${suggestion.name}
                        </p>
                        <div class="d-flex gap-2 align-items-center">
                            <span class="price-tag">€${suggestion.price.toFixed(2)}</span>
                            <span class="stock-indicator ${getStockClass(suggestion.stock)}">
                                ${getStockText(suggestion.stock)}
                            </span>
                            <span class="frequency-badge">
                                ${suggestion.frequency} purchases
                            </span>
                            ${suggestion.category ? `<span class="badge bg-secondary">Category: ${suggestion.category}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Update statistics
function updateStatistics(summary) {
    const container = document.getElementById('statsContent');
    
    const html = `
        <div class="row text-center">
            <div class="col-6 mb-3">
                <div class="h4 mb-1">${summary.total_bundles_analyzed || 0}</div>
                <small>Bundles Analyzed</small>
            </div>
            <div class="col-6 mb-3">
                <div class="h4 mb-1">${summary.total_items_analyzed || 0}</div>
                <small>Items Analyzed</small>
            </div>
            <div class="col-6 mb-3">
                <div class="h4 mb-1">${summary.customer_items_count || 0}</div>
                <small>Customer Items</small>
            </div>
            <div class="col-6 mb-3">
                <div class="h4 mb-1">${summary.recommendations_generated || 0}</div>
                <small>Recommendations</small>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Get stock class for styling
function getStockClass(stock) {
    if (stock > 50) return 'stock-high';
    if (stock > 10) return 'stock-medium';
    return 'stock-low';
}

// Get stock text
function getStockText(stock) {
    if (stock > 50) return 'In Stock';
    if (stock > 10) return 'Limited';
    if (stock > 0) return 'Low Stock';
    return 'Out of Stock';
}

// Show loading spinner
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = show ? 'block' : 'none';
}

// Hide results
function hideResults() {
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
}

// Show no results message
function showNoResults() {
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('noResults').style.display = 'block';
}

// Export results
function exportResults() {
    if (!currentResults) {
        showAlert('No results to export', 'warning');
        return;
    }
    
    const dataStr = JSON.stringify(currentResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `upselling_recommendations_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    showAlert('Results exported successfully', 'success');
}

// Clear results
function clearResults() {
    currentResults = null;
    document.getElementById('customerId').value = '';
    hideResults();
    document.getElementById('statsContent').innerHTML = '<p class="mb-2">Enter a customer ID to see analysis statistics</p>';
    showAlert('Results cleared', 'info');
}

// Show alert message
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
} 