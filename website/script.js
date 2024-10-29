let currentAddButton = null;
let resultsChart = null;
let isEditingCopy = true; // Start as true for new strategies
let originalStrategyId = null;

function showBlockMenu(event, parentBlock) {
    if (!isEditingCopy) {
        return;
    }
    
    event.stopPropagation();
    
    const menu = document.getElementById('block-menu');
    
    if (currentAddButton === event.target) {
        hideBlockMenu();
        return;
    }
    
    const rect = event.target.getBoundingClientRect();
    
    menu.style.display = 'block';
    menu.style.left = `${rect.right + 10}px`;
    menu.style.top = `${rect.top}px`;
    
    const menuRect = menu.getBoundingClientRect();
    if (menuRect.right > window.innerWidth) {
        menu.style.left = `${rect.left - menuRect.width - 10}px`;
    }
    
    currentAddButton = event.target;
    
    const branch = event.target.closest('.left-branch, .right-branch');
    const existingBlocks = branch.querySelectorAll('.block');
    
    const buttons = menu.querySelectorAll('button');
    buttons.forEach(button => {
        button.style.display = existingBlocks.length > 0 ? 'none' : 'block';
    });
    
    document.removeEventListener('click', hideBlockMenu);
    
    setTimeout(() => {
        document.addEventListener('click', hideBlockMenu);
    }, 0);
}

function addBlock(type) {
    if (!isEditingCopy || !currentAddButton) {
        return;
    }
    
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
                <input type="text" value="AAPL" style="width: 60px" oninput="capitalizeAssetInput(this)">
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
            <input type="text" value="QQQ" style="width: 60px" oninput="capitalizeAssetInput(this)">
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

    const menu = document.getElementById('block-menu');
    menu.classList.remove('visible');
    menu.style.left = '-9999px';
    currentAddButton = null;
    document.removeEventListener('click', hideBlockMenu);
}

function hideBlockMenu(event) {
    const menu = document.getElementById('block-menu');
    if (!menu) return;
    
    if (event && (
        event.target.closest('#block-menu') || 
        event.target === currentAddButton
    )) {
        return;
    }
    
    menu.style.display = 'none';
    currentAddButton = null;
    document.removeEventListener('click', hideBlockMenu);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    
    const saveButton = document.getElementById('save-strategy');
    const loadButton = document.getElementById('load-strategy');
    
    if (!saveButton || !loadButton) {
        console.error('Could not find save or load buttons');
        return;
    }
    
    console.log('Found buttons:', { saveButton, loadButton });
    
    saveButton.addEventListener('click', (e) => {
        console.log('Save button clicked');
        saveStrategy();
    });
    
    loadButton.addEventListener('click', (e) => {
        console.log('Load button clicked');
        showLoadStrategyModal();
    });
    
    // Add event listener for modal close button
    const closeButton = document.querySelector('.modal .close');
    if (closeButton) {
        closeButton.addEventListener('click', hideLoadStrategyModal);
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('load-strategy-modal');
        if (event.target === modal) {
            hideLoadStrategyModal();
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

    // Add capitalization to the root block's asset input
    const rootAssetInput = document.querySelector('.root-block input[type="text"]');
    if (rootAssetInput) {
        rootAssetInput.addEventListener('input', function() {
            capitalizeAssetInput(this);
        });
    }

    // Add event listener for make copy button
    const makeCopyBtn = document.getElementById('make-copy');
    if (makeCopyBtn) {
        makeCopyBtn.addEventListener('click', makeStrategyCopy);
    }

    // Start in editing mode for new strategies
    setReadOnlyMode(false);

    // Ensure menu is hidden initially
    const menu = document.getElementById('block-menu');
    if (menu) {
        menu.style.display = 'none';
    }
});

// Delete block function
function deleteBlock(event) {
    if (!isEditingCopy) {
        return;
    }
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

// Add this function to handle the rules parsing
function parseBlock(block) {
    if (!block) return null;

    // Handle IF block
    if (block.querySelector('.if-block')) {
        const ifBlock = block.querySelector('.if-block');
        const indicator = ifBlock.querySelector('.indicator-type').value;
        const paramInputs = Array.from(ifBlock.querySelectorAll('.indicator-params input'));
        const params = paramInputs.map(input => Number(input.value));
        const symbol = ifBlock.querySelector('input[type="text"]').value;
        const comparator = ifBlock.querySelector('.comparator').value;
        const value = Number(ifBlock.querySelector('input[type="number"]:not(.indicator-params input)').value) / 100;

        const branches = block.querySelector('.branches');
        const leftBranch = branches.querySelector('.left-branch');
        const rightBranch = branches.querySelector('.right-branch');

        const ifTrueBlocks = Array.from(leftBranch.querySelectorAll(':scope > .block')).map(parseBlock).filter(Boolean);
        const ifFalseBlocks = Array.from(rightBranch.querySelectorAll(':scope > .block')).map(parseBlock).filter(Boolean);

        return {
            type: 'condition',
            indicator: {
                name: indicator,
                params: params,
                symbol: symbol
            },
            comparator: comparator,
            value: value,
            if_true: ifTrueBlocks,
            if_false: ifFalseBlocks
        };
    }

    // Handle WEIGHT block
    if (block.querySelector('.weight-block')) {
        const weightBlock = block.querySelector('.weight-block');
        const weightType = weightBlock.querySelector('.weight-type').value;
        const assets = Array.from(block.querySelectorAll('.weight-asset')).map(asset => {
            const symbol = asset.querySelector('input[type="text"]').value;
            if (weightType === 'weighted') {
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
    
    loadingIndicator.classList.add('visible');
    resultsContainer.classList.add('visible');
    
    const chartCanvas = document.getElementById('results-chart');
    chartCanvas.style.filter = 'blur(3px)';
    chartCanvas.style.opacity = '0.3';

    const strategyName = document.querySelector('.strategy-name input').value;
    const rootBlock = document.querySelector('.root-block');
    const rules = parseBlock(rootBlock);
    
    if (!rules) {
        alert('Invalid strategy configuration');
        loadingIndicator.classList.remove('visible');
        chartCanvas.style.filter = 'none';
        chartCanvas.style.opacity = '1';
        return;
    }

    const payload = {
        name: strategyName,
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        starting_capital: Number(document.getElementById('starting-capital').value),
        monthly_investment: Number(document.getElementById('monthly-investment').value),
        rules: rules
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
        loadingIndicator.classList.remove('visible');
        chartCanvas.style.filter = 'none';
        chartCanvas.style.opacity = '1';
    }
}

function displayResults(data) {
    const ctx = document.getElementById('results-chart').getContext('2d');
    const resultsContainer = document.getElementById('backtest-results');
    
    // Clear all previous content
    const existingStats = resultsContainer.querySelector('.stats-container');
    const existingNoData = resultsContainer.querySelector('.no-data-message');
    
    if (existingStats) {
        existingStats.remove();
    }
    if (existingNoData) {
        existingNoData.remove();
    }
    
    // Destroy existing chart if it exists
    if (resultsChart) {
        resultsChart.destroy();
    }

    // Check if we have data to display
    if (!data.daily_values?.length || !data.spy_values?.length) {
        // Create a message container
        const noDataMessage = document.createElement('div');
        noDataMessage.className = 'no-data-message';
        noDataMessage.innerHTML = `
            <div class="message-content">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p>No data available for the selected period and assets.</p>
            </div>
        `;
        resultsContainer.appendChild(noDataMessage);
        return;
    }

    // Create stats display
    const statsDiv = document.createElement('div');
    statsDiv.className = 'stats-container';
    
    // Helper function to determine if a value should be shown as a percentage
    const isPercentage = (key) => ["Total Return", "Annualized Return", "Max Drawdown", "Volatility"].includes(key);
    
    // Create stats HTML for metrics
    const metricsHtml = Object.entries(data.stats).map(([key, value]) => `
        <div class="stat-item">
            <div class="stat-label">${key}</div>
            <div class="stat-value ${value >= 0 ? 'positive' : 'negative'}">
                ${isPercentage(key) ? (value).toFixed(2) + '%' : value.toFixed(2)}
            </div>
        </div>
    `).join('');

    // Get the final values
    const lastDataPoint = data.daily_values[data.daily_values.length - 1];
    const lastSpyPoint = data.spy_values[data.spy_values.length - 1];
    
    // Calculate if the values are positive (compared to starting capital)
    const startingCapital = Number(document.getElementById('starting-capital').value);
    const portfolioReturn = ((lastDataPoint.portfolio_value - startingCapital) / startingCapital) * 100;
    const spyReturn = ((lastSpyPoint.SPY - startingCapital) / startingCapital) * 100;

    // Add final values HTML with color classes
    const finalValuesHtml = `
        <div class="stat-item final-value">
            <div class="stat-label">Final Portfolio Value</div>
            <div class="stat-value ${portfolioReturn >= 0 ? 'positive' : 'negative'}">
                $${lastDataPoint.portfolio_value.toLocaleString(undefined, {maximumFractionDigits: 2})}
            </div>
        </div>
        <div class="stat-item final-value">
            <div class="stat-label">SPY Value</div>
            <div class="stat-value ${spyReturn >= 0 ? 'positive' : 'negative'}">
                $${lastSpyPoint.SPY.toLocaleString(undefined, {maximumFractionDigits: 2})}
            </div>
        </div>
    `;

    // Combine metrics and final values with a separator
    statsDiv.innerHTML = `
        <div class="metrics-row">
            ${metricsHtml}
        </div>
        <div class="separator"></div>
        <div class="final-values-row">
            ${finalValuesHtml}
        </div>
    `;
    
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

// Update the capitalization function to maintain cursor position
function capitalizeAssetInput(input) {
    const start = input.selectionStart;
    const end = input.selectionEnd;
    input.value = input.value.toUpperCase();
    input.setSelectionRange(start, end);
}

// Add these functions near the top of the file
function showLoadStrategyModal() {
    console.log('Showing modal');
    const modal = document.getElementById('load-strategy-modal');
    if (!modal) {
        console.error('Could not find modal element');
        return;
    }
    modal.style.display = 'block';
    loadStrategiesList();
}

function hideLoadStrategyModal() {
    const modal = document.getElementById('load-strategy-modal');
    modal.style.display = 'none';
}

async function loadStrategiesList() {
    const strategiesList = document.querySelector('.strategies-list');
    strategiesList.innerHTML = '<div class="loading">Loading strategies...</div>';
    
    try {
        console.log('Fetching strategies...');
        const response = await fetch('http://localhost:8000/get_all_strategies');
        console.log('Load response:', response);
        
        const strategies = await response.json();
        console.log('Loaded strategies:', strategies);
        
        if (strategies && strategies.length > 0) {
            strategiesList.innerHTML = strategies.map(strategy => `
                <div class="strategy-item" data-id="${strategy.id}" onclick="loadStrategy(${strategy.id})">
                    <div class="strategy-item-name">${strategy.name}</div>
                    <div class="strategy-item-date">Created: ${new Date(strategy.created_at).toLocaleDateString()}</div>
                </div>
            `).join('');
        } else {
            strategiesList.innerHTML = '<div class="no-strategies">No saved strategies found</div>';
        }
    } catch (error) {
        console.error('Error loading strategies:', error);
        strategiesList.innerHTML = '<div class="error">Error loading strategies: ' + error.message + '</div>';
    }
}

async function loadStrategy(strategyId) {
    try {
        const response = await fetch(`http://localhost:8000/get_strategy?strategy_id=${strategyId}`);
        const strategy = await response.json();
        
        if (strategy) {
            // Store the original strategy ID
            originalStrategyId = strategy.id;
            
            // Update strategy name
            const nameInput = document.querySelector('.strategy-name input');
            nameInput.value = strategy.name;
            
            // Set to read-only mode
            setReadOnlyMode(true);
            
            // Parse the rules if they're a string
            const rules = typeof strategy.rules === 'string' 
                ? JSON.parse(strategy.rules) 
                : strategy.rules;
            
            // Rebuild the UI with the rules
            rebuildStrategyUI(rules);
            
            hideLoadStrategyModal();
        }
    } catch (error) {
        console.error('Error loading strategy:', error);
        alert('Error loading strategy');
    }
}

async function saveStrategy() {
    if (!isEditingCopy) {
        alert('Please make a copy before editing this strategy');
        return;
    }

    const strategyNameInput = document.querySelector('.strategy-name input');
    const rootBlock = document.querySelector('.root-block');
    
    if (!strategyNameInput || !rootBlock) {
        alert('Missing required elements');
        return;
    }

    const rules = parseBlock(rootBlock);
    if (!rules) {
        alert('Invalid strategy configuration');
        return;
    }

    const strategy = {
        name: strategyNameInput.value,
        rules: rules,
        user_id: 1
    };

    try {
        const response = await fetch('http://localhost:8000/save_strategy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(strategy)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            alert('Strategy saved successfully!');
            originalStrategyId = result.strategy_id;
            setReadOnlyMode(true);
        } else {
            alert('Error saving strategy');
        }
    } catch (error) {
        console.error('Error saving strategy:', error);
        alert('Error saving strategy: ' + error.message);
    }
}

// Add this to your DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    // ... existing code ...
    
    // Add event listeners for save and load buttons
    document.getElementById('save-strategy').addEventListener('click', saveStrategy);
    document.getElementById('load-strategy').addEventListener('click', showLoadStrategyModal);
    
    // Add event listener for modal close button
    document.querySelector('.modal .close').addEventListener('click', hideLoadStrategyModal);
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('load-strategy-modal');
        if (event.target === modal) {
            hideLoadStrategyModal();
        }
    });
});

// Add this function to rebuild the strategy UI
function rebuildStrategyUI(rules) {
    // Clear existing strategy
    const strategyRoot = document.getElementById('strategy-root');
    strategyRoot.innerHTML = '';
    
    // If rules has a nested rules property, use that
    const actualRules = rules.rules || rules;
    
    // Rebuild the UI based on the rules
    const rootBlock = buildBlockFromRules(actualRules);
    if (rootBlock) {
        rootBlock.className = 'block root-block';
        strategyRoot.appendChild(rootBlock);
    }
}

function buildBlockFromRules(rules) {
    if (!rules) return null;

    const block = document.createElement('div');
    block.className = 'block';
    
    if (rules.type === 'condition') {
        // Build IF block
        const blockContent = document.createElement('div');
        blockContent.className = 'block-content if-block';
        blockContent.innerHTML = `
            <span>IF</span>
            <select class="indicator-type" onchange="updateIndicatorParams(this)">
                <option value="${rules.indicator.name}">${rules.indicator.name}</option>
            </select>
            <div class="indicator-params">
                ${rules.indicator.params.map(param => `
                    <input type="number" value="${param}" style="width: 40px">
                `).join('')}
                <span>d of</span>
            </div>
            <input type="text" value="${rules.indicator.symbol}" style="width: 60px">
            <span>is</span>
            <select class="comparator">
                <option value="${rules.comparator}">${rules.comparator}</option>
            </select>
            <input type="number" value="${rules.value * 100}" style="width: 50px">
            <span>%</span>
        `;
        
        const branches = document.createElement('div');
        branches.className = 'branches';
        branches.innerHTML = `
            <div class="left-branch">
                ${rules.if_true ? '' : '<button class="add-block" onclick="showBlockMenu(event, \'left\')">+</button>'}
            </div>
            <div class="right-branch">
                <div class="block-content else-block">
                    <span>ELSE</span>
                </div>
                ${rules.if_false ? '' : '<button class="add-block" onclick="showBlockMenu(event, \'right\')">+</button>'}
            </div>
        `;
        
        block.appendChild(blockContent);
        block.appendChild(branches);
        
        // Recursively build true/false branches
        if (rules.if_true && rules.if_true.length > 0) {
            const trueBlock = buildBlockFromRules(rules.if_true[0]);
            if (trueBlock) {
                branches.querySelector('.left-branch').appendChild(trueBlock);
            }
        }
        
        if (rules.if_false && rules.if_false.length > 0) {
            const falseBlock = buildBlockFromRules(rules.if_false[0]);
            if (falseBlock) {
                branches.querySelector('.right-branch').appendChild(falseBlock);
            }
        }
    } else if (rules.type === 'weight') {
        // Build WEIGHT block
        const blockContent = document.createElement('div');
        blockContent.className = 'block-content weight-block';
        blockContent.innerHTML = `
            <button class="delete-button">×</button>
            <span>WEIGHT</span>
            <select class="weight-type">
                <option value="${rules.weight_type}">${rules.weight_type}</option>
            </select>
        `;
        
        const assetsContainer = document.createElement('div');
        assetsContainer.className = 'weight-assets';
        
        rules.assets.forEach(asset => {
            const assetDiv = document.createElement('div');
            assetDiv.className = 'weight-asset';
            assetDiv.innerHTML = `
                <button class="delete-button">×</button>
                <input type="text" value="${asset.symbol}" style="width: 60px">
                ${rules.weight_type === 'weighted' ? `
                    <span>:</span>
                    <input type="number" value="${asset.weight * 100}" style="width: 50px">
                    <span>%</span>
                ` : ''}
            `;
            assetsContainer.appendChild(assetDiv);
        });
        
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
        
        block.appendChild(blockContent);
        block.appendChild(assetsContainer);
        block.appendChild(addAssetButton);
    }
    
    return block;
}

// Add function to handle read-only mode
function setReadOnlyMode(readonly) {
    isEditingCopy = !readonly;
    
    // Update name input
    const nameInput = document.querySelector('.strategy-name input');
    nameInput.readOnly = readonly;
    
    // Show/hide make copy button
    const makeCopyBtn = document.getElementById('make-copy');
    makeCopyBtn.style.display = readonly ? 'block' : 'none';
    
    // Show/hide save button
    const saveBtn = document.getElementById('save-strategy');
    saveBtn.style.display = readonly ? 'none' : 'block';
    
    // Disable/enable all inputs and selects in the strategy builder
    const inputs = document.querySelectorAll('#strategy-root input, #strategy-root select');
    inputs.forEach(input => {
        input.disabled = readonly;
    });
    
    // Disable/enable add and delete buttons
    const actionButtons = document.querySelectorAll('#strategy-root .add-block, #strategy-root .delete-button');
    actionButtons.forEach(button => {
        if (readonly) {
            button.style.display = 'none';
            // Remove click handlers
            button.onclick = null;
        } else {
            button.style.display = 'block';
            // Restore click handlers for add buttons
            if (button.classList.contains('add-block')) {
                button.onclick = (e) => showBlockMenu(e, button.closest('.left-branch, .right-branch'));
            }
        }
    });
    
    // Disable/enable block menu
    const blockMenu = document.getElementById('block-menu');
    if (blockMenu) {
        blockMenu.style.display = readonly ? 'none' : 'block';
    }
}

// Add function to make a copy
function makeStrategyCopy() {
    const nameInput = document.querySelector('.strategy-name input');
    nameInput.value = `Copy of ${nameInput.value}`;
    originalStrategyId = null;
    setReadOnlyMode(false);
}
