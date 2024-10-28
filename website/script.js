let currentAddButton = null;
let resultsChart = null;

function showBlockMenu(event, parentBlock) {
    const menu = document.getElementById('block-menu');
    const rect = event.target.getBoundingClientRect();
    
    menu.style.left = `${rect.right + 10}px`;
    menu.style.top = `${rect.top}px`;
    
    const menuRect = menu.getBoundingClientRect();
    if (menuRect.right > window.innerWidth) {
        menu.style.left = `${rect.left - menuRect.width - 10}px`;
    }
    
    menu.classList.add('visible');
    currentAddButton = event.target;
    
    const branch = event.target.closest('.left-branch, .right-branch');
    const existingBlocks = branch.querySelectorAll('.block');
    
    const buttons = menu.querySelectorAll('button');
    buttons.forEach(button => {
        button.style.display = existingBlocks.length > 0 ? 'none' : 'block';
    });
    
    event.stopPropagation();
    document.addEventListener('click', hideBlockMenu);
}

function addBlock(type) {
    if (!currentAddButton) return;
    
    const branch = currentAddButton.closest('.left-branch, .right-branch');
    if (!branch) return;

    const newBlock = document.createElement('div');
    newBlock.className = 'block';
    
    const blockContent = document.createElement('div');
    blockContent.className = 'block-content';
    
    if (type === 'weight') {
        blockContent.classList.add('weight-block');
        blockContent.innerHTML = `
            <button class="delete-button">×</button>
            <span>WEIGHT</span>
            <select class="weight-type">
                <option value="equal">Equal</option>
                <option value="weighted">Weighted</option>
            </select>
        `;

        const assetsContainer = document.createElement('div');
        assetsContainer.className = 'weight-assets';
        
        const addAssetButton = document.createElement('button');
        addAssetButton.className = 'add-block';
        addAssetButton.innerHTML = '+';
        addAssetButton.onclick = (e) => {
            e.stopPropagation();
            const weightType = blockContent.querySelector('.weight-type').value;
            const newAsset = document.createElement('div');
            newAsset.className = 'weight-asset';
            newAsset.innerHTML = `
                <button class="delete-button">×</button>
                <input type="text" value="AAPL" style="width: 60px">
                ${weightType === 'weighted' ? `
                    <span>:</span>
                    <input type="number" value="50" style="width: 50px">
                    <span>%</span>
                ` : ''}
            `;
            assetsContainer.appendChild(newAsset);
        };
        
        newBlock.appendChild(blockContent);
        newBlock.appendChild(assetsContainer);
        newBlock.appendChild(addAssetButton);
    } else if (type === 'if') {
        blockContent.classList.add('if-block');
        blockContent.innerHTML = `
            <button class="delete-button">×</button>
            <span>IF</span>
            <select class="indicator-type" onchange="updateIndicatorParams(this)">
                <option value="cumulative_return">Cumulative Return</option>
                <option value="rsi">RSI</option>
                <option value="sma_price">SMA Price</option>
                <option value="macd">MACD</option>
                <option value="ema">EMA</option>
                <option value="fibonacci">Fibonacci</option>
            </select>
            <div class="indicator-params">
                <input type="number" value="5" style="width: 40px">
                <span>d of</span>
            </div>
            <input type="text" value="QQQ" style="width: 60px">
            <span>is</span>
            <select class="comparator">
                <option value="<">less than</option>
                <option value=">">greater than</option>
                <option value="==">equal to</option>
                <option value=">=">greater or equal</option>
                <option value="<=">less or equal</option>
            </select>
            <input type="number" value="5" style="width: 50px">
            <span>%</span>
        `;

        const branches = document.createElement('div');
        branches.className = 'branches';
        branches.innerHTML = `
            <div class="left-branch">
                <button class="add-block" onclick="showBlockMenu(event, 'left')">+</button>
            </div>
            <div class="right-branch">
                <div class="block-content else-block">
                    <span>ELSE</span>
                </div>
                <button class="add-block" onclick="showBlockMenu(event, 'right')">+</button>
            </div>
        `;
        newBlock.appendChild(branches);
    }
    
    newBlock.insertBefore(blockContent, newBlock.firstChild);
    branch.insertBefore(newBlock, currentAddButton);
    currentAddButton.remove();
    hideBlockMenu();
}

function hideBlockMenu() {
    const menu = document.getElementById('block-menu');
    menu.classList.remove('visible');
    currentAddButton = null;
    document.removeEventListener('click', hideBlockMenu);
}

document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', (event) => {
        if (!event.target.closest('.block-menu') && !event.target.closest('.add-block')) {
            hideBlockMenu();
        }
    });

    const runButton = document.getElementById('run-backtest');
    runButton.addEventListener('click', runBacktest);
    
    // Set default dates
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    document.getElementById('start-date').value = oneYearAgo.toISOString().split('T')[0];
    document.getElementById('end-date').value = today.toISOString().split('T')[0];

    // Add event listener for delete buttons
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('delete-button')) {
            const asset = event.target.closest('.weight-asset');
            if (asset) {
                asset.remove();
            } else {
                deleteBlock(event);
            }
        }
    });

    // Add event listener for weight type changes
    document.addEventListener('change', (event) => {
        const target = event.target;
        if (target.matches('select.weight-type')) {
            const weightBlock = target.closest('.weight-block');
            const assetsContainer = weightBlock.parentElement.parentElement.querySelector('.weight-assets');
            const weightType = target.value;
            
            // Update all assets to show/hide weight inputs
            assetsContainer.querySelectorAll('.weight-asset').forEach(asset => {
                const symbol = asset.querySelector('input[type="text"]').value;
                asset.innerHTML = `
                    <button class="delete-button">×</button>
                    <input type="text" value="${symbol}" style="width: 60px">
                    ${weightType === 'weighted' ? `
                        <span>:</span>
                        <input type="number" value="50" style="width: 50px">
                        <span>%</span>
                    ` : ''}
                `;
            });
        }
    });
});

// Delete block function
function deleteBlock(event) {
    const block = event.target.closest('.block');
    if (block) {
        const parentBranch = block.closest('.left-branch, .right-branch');
        const addButton = document.createElement('button');
        addButton.className = 'add-block';
        addButton.innerHTML = '+';
        addButton.onclick = (e) => showBlockMenu(e, parentBranch);
        parentBranch.appendChild(addButton);
        block.remove();
    }
}

// Event listener for delete buttons
document.addEventListener('click', (event) => {
    if (event.target.classList.contains('delete-button')) {
        const asset = event.target.closest('.weight-asset');
        if (asset) {
            asset.remove(); // Remove only the asset
        } else {
            deleteBlock(event); // Remove the block
        }
    }
});

// Add this function to generate JSON for the strategy
function generateStrategyJSON() {
    const strategyName = document.querySelector('.strategy-name input').value;
    const rootBlock = document.querySelector('.root-block');
    
    const json = {
        name: strategyName,
        rules: parseBlock(rootBlock)
    };
    
    // Update the JSON output textarea
    const jsonOutput = document.getElementById('json-output');
    jsonOutput.value = JSON.stringify(json, null, 2);
    
    // Auto-resize after updating content
    autoResizeTextarea();
}

// Helper function to parse a block and its children
function parseBlock(block) {
    if (!block) return null;

    // Handle IF blocks
    if (block.querySelector('.if-block')) {
        const ifBlock = block.querySelector('.if-block');
        const indicator = ifBlock.querySelector('.indicator-type').value;
        const paramInputs = Array.from(ifBlock.querySelectorAll('.indicator-params input'));
        const params = paramInputs.map(input => Number(input.value));
        const symbol = ifBlock.querySelector('input[type="text"]').value;
        const comparator = ifBlock.querySelector('.comparator').value;
        // Divide the value by 100 since it's a percentage
        const value = Number(ifBlock.querySelector('input[type="number"]:not(.indicator-params input)').value) / 100;

        const branches = block.querySelector('.branches');
        const leftBranch = branches.querySelector('.left-branch');
        const rightBranch = branches.querySelector('.right-branch');

        return {
            type: 'condition',
            indicator: {
                name: indicator,
                params: params,
                symbol: symbol
            },
            comparator: comparator,
            value: value,
            if_true: parseBlocks(leftBranch.querySelectorAll(':scope > .block')),
            if_false: parseBlocks(rightBranch.querySelectorAll(':scope > .block'))
        };
    }
    
    // Handle WEIGHT blocks
    if (block.querySelector('.weight-block')) {
        const weightBlock = block.querySelector('.weight-block');
        const weightType = weightBlock.querySelector('.weight-type').value;
        const assets = Array.from(block.querySelectorAll('.weight-asset')).map(asset => {
            const symbol = asset.querySelector('input[type="text"]').value;
            if (weightType === 'weighted') {
                // Divide the weight by 100 since it's a percentage
                const weight = Number(asset.querySelector('input[type="number"]').value) / 100;
                return { symbol, weight };
            }
            return { symbol };
        });

        return {
            type: 'weight',
            weight_type: weightType,
            assets: assets
        };
    }

    return null;
}

// Helper function to parse multiple blocks
function parseBlocks(blocks) {
    return Array.from(blocks).map(block => parseBlock(block)).filter(Boolean);
}

// Add event listeners for input changes
document.addEventListener('change', (event) => {
    const target = event.target;
    if (target.matches('select.weight-type')) {
        const weightBlock = target.closest('.weight-block');
        const assetsContainer = weightBlock.parentElement.parentElement.querySelector('.weight-assets');
        const weightType = target.value;
        
        // Update all assets to show/hide weight inputs
        assetsContainer.querySelectorAll('.weight-asset').forEach(asset => {
            const symbol = asset.querySelector('input[type="text"]').value;
            asset.innerHTML = `
                <button class="delete-button">×</button>
                <input type="text" value="${symbol}" style="width: 60px">
                ${weightType === 'weighted' ? `
                    <span>:</span>
                    <input type="number" value="50" style="width: 50px">
                    <span>%</span>
                ` : ''}
            `;
        });
        generateStrategyJSON();
    } else if (target.matches('select.indicator-type, select.comparator, input[type="number"], input[type="text"]')) {
        // This will catch all input changes in IF blocks and weight blocks
        generateStrategyJSON();
    }
});

// Also add input event listener for real-time updates
document.addEventListener('input', (event) => {
    const target = event.target;
    if (target.matches('input[type="number"], input[type="text"]')) {
        generateStrategyJSON();
    }
});

// Generate initial JSON when page loads
document.addEventListener('DOMContentLoaded', () => {
    // ... existing DOMContentLoaded code ...
    
    generateStrategyJSON();
});

// Add copy button functionality
const copyButton = document.getElementById('copy-json');
copyButton.addEventListener('click', () => {
    const jsonOutput = document.getElementById('json-output');
    jsonOutput.select();
    document.execCommand('copy');
    
    // Visual feedback
    copyButton.textContent = 'Copied!';
    setTimeout(() => {
        copyButton.textContent = 'Copy';
    }, 2000);
});

// Add this function to automatically resize the textarea
function autoResizeTextarea() {
    const textarea = document.getElementById('json-output');
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    // Set the height to match the content
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Add this new function to handle indicator parameter changes
function updateIndicatorParams(select) {
    const paramsDiv = select.nextElementSibling;
    const indicator = select.value;
    
    if (indicator === 'macd') {
        paramsDiv.innerHTML = `
            <input type="number" value="12" style="width: 40px">
            <span>fast,</span>
            <input type="number" value="26" style="width: 40px">
            <span>slow,</span>
            <input type="number" value="9" style="width: 40px">
            <span>signal of</span>
        `;
    } else {
        paramsDiv.innerHTML = `
            <input type="number" value="5" style="width: 40px">
            <span>d of</span>
        `;
    }
}

// Remove the JSON-related functions and event listeners
// Add this new function for running the backtest

async function runBacktest() {
    const resultsContainer = document.getElementById('backtest-results');
    const loadingIndicator = document.getElementById('chart-loading');
    
    // Show loading indicator
    loadingIndicator.classList.add('visible');
    resultsContainer.classList.add('visible');
    
    const strategyName = document.querySelector('.strategy-name input').value;
    const rootBlock = document.querySelector('.root-block');
    
    const payload = {
        name: strategyName,
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        starting_capital: Number(document.getElementById('starting-capital').value),
        monthly_investment: Number(document.getElementById('monthly-investment').value),
        rules: {
            name: strategyName,
            rules: parseBlock(rootBlock)
        }
    };

    try {
        const response = await fetch('http://localhost:8000/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        displayResults(results);
    } catch (error) {
        console.error('Error:', error);
        alert('Error running backtest: ' + error.message);
    } finally {
        // Hide loading indicator
        loadingIndicator.classList.remove('visible');
    }
}

function displayResults(data) {
    const ctx = document.getElementById('results-chart').getContext('2d');
    const resultsContainer = document.getElementById('backtest-results');
    
    // Clear previous results
    const existingStats = resultsContainer.querySelector('.stats-container');
    if (existingStats) {
        existingStats.remove();
    }
    
    // Destroy existing chart if it exists
    if (resultsChart) {
        resultsChart.destroy();
    }

    // Create stats display
    const statsDiv = document.createElement('div');
    statsDiv.className = 'stats-container';
    
    // Helper function to determine if a value should be shown as a percentage
    const isPercentage = (key) => ["Total Return", "Annualized Return", "Max Drawdown", "Volatility"].includes(key);
    
    // Create stats HTML
    statsDiv.innerHTML = Object.entries(data.stats).map(([key, value]) => `
        <div class="stat-item">
            <div class="stat-label">${key}</div>
            <div class="stat-value ${value >= 0 ? 'positive' : 'negative'}">
                ${isPercentage(key) ? (value).toFixed(2) + '%' : value.toFixed(2)}
            </div>
        </div>
    `).join('');
    
    // Insert stats before the chart
    const chartCanvas = document.getElementById('results-chart');
    resultsContainer.insertBefore(statsDiv, chartCanvas);

    // Prepare data for chart - using last available value for nulls
    let lastPortfolioValue = null;
    let lastSpyValue = null;

    const chartData = data.daily_values.map((row, index) => {
        // Use last known value if current value is null
        if (row.portfolio_value !== null) {
            lastPortfolioValue = row.portfolio_value;
        }
        
        const spyValue = data.spy_values[index].SPY;
        if (spyValue !== null) {
            lastSpyValue = spyValue;
        }

        return {
            date: row.date,
            portfolio: lastPortfolioValue,
            spy: lastSpyValue
        };
    }).filter(row => row.portfolio !== null && row.spy !== null);

    // Create new chart
    resultsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.map(row => row.date),
            datasets: [
                {
                    label: 'Portfolio',
                    data: chartData.map(row => row.portfolio),
                    borderColor: '#1976D2',
                    backgroundColor: 'rgba(25, 118, 210, 0.1)',
                    fill: true,
                    tension: 0.1,
                    borderWidth: 2,
                    order: 1
                },
                {
                    label: 'SPY',
                    data: chartData.map(row => row.spy),
                    borderColor: '#FFA726',
                    backgroundColor: 'rgba(255, 167, 38, 0.1)',
                    fill: true,
                    tension: 0.1,
                    borderWidth: 2,
                    order: 2
                }
            ]
        },
        options: {
            layout: {
                padding: {
                    top: 20,
                    right: 20,
                    bottom: 20,
                    left: 20
                }
            },
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            scales: {
                x: {
                    grid: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: true,
                        maxTicksLimit: 8,
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    grid: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        callback: (value) => '$' + value.toLocaleString()
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 14
                    },
                    callbacks: {
                        label: (context) => {
                            return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            }
        }
    });
}

// Add event listener for the run backtest button
document.addEventListener('DOMContentLoaded', () => {
    const runButton = document.getElementById('run-backtest');
    runButton.addEventListener('click', runBacktest);
    
    // Set default dates
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    document.getElementById('start-date').value = oneYearAgo.toISOString().split('T')[0];
    document.getElementById('end-date').value = today.toISOString().split('T')[0];
});
