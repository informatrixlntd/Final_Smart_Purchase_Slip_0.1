console.log('🚀 script.js loaded successfully at ' + new Date().toISOString());

// Global function for inline onclick fallback
window.handleSaveGodown = function() {
    console.log('🎯 GLOBAL handleSaveGodown called');
    const godownInput = document.getElementById('paddy_unloading_godown');
    const godownDatalist = document.getElementById('godownList');
    const saveGodownBtn = document.getElementById('saveGodownBtn');

    if (!godownInput) {
        console.error('❌ godownInput not found');
        alert('Error: Godown input field not found');
        return;
    }

    const enteredValue = godownInput.value.trim();
    console.log('📝 Entered value:', enteredValue);

    if (!enteredValue) {
        alert('Please enter a godown name');
        return;
    }

    // Save to backend
    saveGodownBtn.disabled = true;
    saveGodownBtn.textContent = 'Saving...';

    fetch('/api/unloading-godowns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: enteredValue })
    })
    .then(response => {
        console.log('✅ Response status:', response.status);
        return response.json();
    })
    .then(result => {
        console.log('✅ Response data:', result);
        if (result.success) {
            // Update dropdown
            if (result.godowns && Array.isArray(result.godowns)) {
                godownDatalist.innerHTML = '';
                result.godowns.forEach(godown => {
                    const option = document.createElement('option');
                    option.value = godown.name;
                    godownDatalist.appendChild(option);
                });
            }
            alert(`✅ Godown "${enteredValue}" saved successfully!`);
            console.log('✅ Godown saved and dropdown updated');
        } else {
            alert('❌ Error saving godown: ' + result.message);
        }
    })
    .catch(error => {
        console.error('❌ Error:', error);
        alert('❌ Error saving godown. Please try again.\n\nDetails: ' + error.message);
    })
    .finally(() => {
        saveGodownBtn.disabled = false;
        saveGodownBtn.textContent = 'Save New Godown';
    });
};

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOMContentLoaded event fired');
    const form = document.getElementById('purchaseForm');
    const dateInput = document.getElementById('date');
    const billNoInput = document.getElementById('bill_no');
    const clearBtn = document.getElementById('clearBtn');

    const bags = document.getElementById('bags');
    const netWeightKg = document.getElementById('net_weight_kg');
    const gunnyWeightKg = document.getElementById('gunny_weight_kg');
    const finalWeightKg = document.getElementById('final_weight_kg');
    const weightQuintal = document.getElementById('weight_quintal');
    const weightKhandi = document.getElementById('weight_khandi');
    const avgBagWeight = document.getElementById('avg_bag_weight');
    const rateBasis = document.getElementById('rate_basis');
    const rateValue = document.getElementById('rate_value');
    const totalPurchaseAmount = document.getElementById('total_purchase_amount');
    const bankCommission = document.getElementById('bank_commission');
    const postage = document.getElementById('postage');
    const freight = document.getElementById('freight');
    const rateDiff = document.getElementById('rate_diff');
    const qualityDiff = document.getElementById('quality_diff');
    const moistureDed = document.getElementById('moisture_ded');
    const tds = document.getElementById('tds');
    const batavPercent = document.getElementById('batav_percent');
    const batav = document.getElementById('batav');
    const dalaliRate = document.getElementById('dalali_rate');
    const dalali = document.getElementById('dalali');
    const hammaliRate = document.getElementById('hammali_rate');
    const hammali = document.getElementById('hammali');
    const totalDeduction = document.getElementById('total_deduction');
    const payableAmount = document.getElementById('payable_amount');
    const paymentAmount = document.getElementById('payment_amount');

    const now = new Date();
    const istOffset = 5.5 * 60 * 60 * 1000;
    const istTime = new Date(now.getTime() + istOffset);
    dateInput.value = istTime.toISOString().slice(0, 16);
    fetchNextBillNo();

    function fetchNextBillNo() {
        fetch('/api/next-bill-no')
            .then(response => response.json())
            .then(data => {
                billNoInput.value = data.bill_no;
            })
            .catch(error => {
                console.error('Error fetching bill number:', error);
                billNoInput.value = '1';
            });
    }

    function calculateWeightFields() {
        const netKg = parseFloat(netWeightKg.value) || 0;
        const gunnyKg = parseFloat(gunnyWeightKg.value) || 0;
        const bagsVal = parseFloat(bags.value) || 0;

        const finalKg = Math.max(0, netKg - gunnyKg);
        const quintal = finalKg / 100;
        const khandi = finalKg / 150;
        const avgBag = bagsVal > 0 ? (finalKg / bagsVal) : 0;

        finalWeightKg.value = finalKg.toFixed(2);
        weightQuintal.value = quintal.toFixed(3);
        weightKhandi.value = khandi.toFixed(3);
        avgBagWeight.value = avgBag.toFixed(2);

        return { finalKg, quintal, khandi };
    }

    function calculateTotalPurchaseAmount() {
        const weights = calculateWeightFields();
        const rateBasisVal = rateBasis.value;
        const rateVal = parseFloat(rateValue.value) || 0;

        let totalAmount = 0;
        if (rateBasisVal === 'Quintal') {
            totalAmount = weights.quintal * rateVal;
        } else if (rateBasisVal === 'Khandi') {
            totalAmount = weights.khandi * rateVal;
        }

        totalPurchaseAmount.value = totalAmount.toFixed(2);
        return totalAmount;
    }

    function calculateFields() {
        const totalAmount = calculateTotalPurchaseAmount();
        const rateBasisVal = rateBasis.value;
        const quintal = parseFloat(weightQuintal.value) || 0;
        const khandi = parseFloat(weightKhandi.value) || 0;

        const bankCommissionVal = parseFloat(bankCommission.value) || 0;
        const postageVal = parseFloat(postage.value) || 0;
        const freightVal = parseFloat(freight.value) || 0;
        const rateDiffVal = parseFloat(rateDiff.value) || 0;
        const qualityDiffVal = parseFloat(qualityDiff.value) || 0;
        const moistureDedVal = parseFloat(moistureDed.value) || 0;
        const tdsVal = parseFloat(tds.value) || 0;

        const batavPercentVal = parseFloat(batavPercent.value) || 0;
        const dalaliRateVal = parseFloat(dalaliRate.value) || 0;
        const hammaliRateVal = parseFloat(hammaliRate.value) || 0;

        const batavVal = batavPercentVal > 0 ? (totalAmount * (batavPercentVal / 100)) : 0;

        // NEW CALCULATION: Dalali & Hamali based on Net Weight KG / 100 (not rate basis)
        const netKg = parseFloat(netWeightKg.value) || 0;
        const dalaliVal = dalaliRateVal > 0 ? ((netKg / 100) * dalaliRateVal) : 0;
        const hammaliVal = hammaliRateVal > 0 ? ((netKg / 100) * hammaliRateVal) : 0;

        const categoryADeductions = bankCommissionVal + postageVal + freightVal + rateDiffVal + qualityDiffVal + moistureDedVal + tdsVal;
        const totalDeductionVal = categoryADeductions + batavVal + dalaliVal + hammaliVal;

        const payableAmountVal = totalAmount - totalDeductionVal;

        batav.value = batavVal.toFixed(2);
        dalali.value = dalaliVal.toFixed(2);
        hammali.value = hammaliVal.toFixed(2);
        totalDeduction.value = totalDeductionVal.toFixed(2);
        payableAmount.textContent = payableAmountVal.toFixed(2);
        paymentAmount.value = payableAmountVal.toFixed(2);
    }

    netWeightKg.addEventListener('input', calculateFields);
    gunnyWeightKg.addEventListener('input', calculateFields);
    bags.addEventListener('input', calculateFields);
    rateBasis.addEventListener('change', calculateFields);
    rateValue.addEventListener('input', calculateFields);

    document.querySelectorAll('.calc-input').forEach(input => {
        input.addEventListener('input', calculateFields);
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Prevent double submission
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';
        }

        const formData = new FormData(form);
        const data = {};

        formData.forEach((value, key) => {
            data[key] = value;
        });

        data['net_weight_kg'] = netWeightKg.value;
        data['gunny_weight_kg'] = gunnyWeightKg.value;
        data['final_weight_kg'] = finalWeightKg.value;
        data['weight_quintal'] = weightQuintal.value;
        data['weight_khandi'] = weightKhandi.value;
        data['avg_bag_weight'] = avgBagWeight.value;
        data['rate_basis'] = rateBasis.value;
        data['rate_value'] = rateValue.value;
        data['total_purchase_amount'] = totalPurchaseAmount.value;
        data['batav'] = batav.value;
        data['dalali'] = dalali.value;
        data['hammali'] = hammali.value;
        data['total_deduction'] = totalDeduction.value;
        data['payable_amount'] = payableAmount.textContent;

        try {
            const response = await fetch('/api/add-slip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }

            const result = await response.json();

            if (result.success) {
                // NEW WORKFLOW: Save only (no automatic PDF)
                // 1. Store newly created slip ID for highlighting
                sessionStorage.setItem('newlyCreatedSlipId', result.slip_id);

                // 2. Redirect to View All Slips
                // User can manually print from there if needed
                window.location.href = '/app#view';
            } else {
                throw new Error(result.message || 'Failed to save slip');
            }
        } catch (error) {
            console.error('[ERROR] Error saving slip:', error);
            alert('Error saving purchase slip: ' + error.message);

            // Re-enable submit button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save';
            }
        }
    });

    clearBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear the form?')) {
            form.reset();
            const now = new Date();
            const istOffset = 5.5 * 60 * 60 * 1000;
            const istTime = new Date(now.getTime() + istOffset);
            dateInput.value = istTime.toISOString().slice(0, 16);
            fetchNextBillNo();
            calculateFields();
        }
    });

    calculateCalculatedRate();
    calculateFields();

    // ===== DYNAMIC GODOWN DROPDOWN =====
    const godownInput = document.getElementById('paddy_unloading_godown');
    const godownDatalist = document.getElementById('godownList');
    const saveGodownBtn = document.getElementById('saveGodownBtn');
    let allGodowns = [];

    console.log('Godown elements:', {
        input: godownInput ? 'found' : 'NOT FOUND',
        datalist: godownDatalist ? 'found' : 'NOT FOUND',
        button: saveGodownBtn ? 'found' : 'NOT FOUND'
    });

    // Load existing godowns on page load
    async function loadGodowns() {
        try {
            console.log('📥 Fetching godowns from /api/unloading-godowns...');
            const response = await fetch('/api/unloading-godowns');
            console.log('Response status:', response.status);

            const result = await response.json();
            console.log('Response data:', result);

            if (result.success && result.godowns) {
                allGodowns = result.godowns;
                updateGodownDatalist();
                console.log(`✓ Loaded ${allGodowns.length} godowns:`, allGodowns);
            } else {
                console.warn('No godowns returned from API:', result);
                allGodowns = [];
            }
        } catch (error) {
            console.error('❌ Error loading godowns:', error);
            allGodowns = [];
        }
    }

    // Update datalist with godown options
    function updateGodownDatalist() {
        if (!godownDatalist) {
            console.error('❌ godownDatalist element not found!');
            return;
        }

        godownDatalist.innerHTML = '';
        allGodowns.forEach(godown => {
            const option = document.createElement('option');
            option.value = godown.name;
            godownDatalist.appendChild(option);
        });
        console.log(`✓ Updated datalist with ${allGodowns.length} options`);
    }

    // Save new godown when button is clicked
    async function saveNewGodown() {
        console.log('🔘 Save Godown button clicked');

        if (!godownInput) {
            console.error('❌ godownInput element not found!');
            alert('Error: Godown input field not found');
            return;
        }

        const enteredValue = godownInput.value.trim();
        console.log('Entered value:', enteredValue);

        if (!enteredValue) {
            alert('Please enter a godown name');
            return;
        }

        // Check if it already exists in the list
        const exists = allGodowns.some(g => g.name.toLowerCase() === enteredValue.toLowerCase());

        if (exists) {
            alert('This godown already exists in the list');
            return;
        }

        // Add new godown to database
        try {
            saveGodownBtn.disabled = true;
            saveGodownBtn.textContent = 'Saving...';

            console.log('📤 Sending POST request to /api/unloading-godowns with:', { name: enteredValue });

            const response = await fetch('/api/unloading-godowns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: enteredValue })
            });

            console.log('Response status:', response.status);
            const result = await response.json();
            console.log('Response data:', result);

            if (result.success) {
                console.log(`✓ Added new godown: ${enteredValue}`);
                if (result.godowns && Array.isArray(result.godowns)) {
                    allGodowns = result.godowns;
                } else if (result.godown) {
                    allGodowns.push(result.godown);
                }
                updateGodownDatalist();
                alert(`Godown "${enteredValue}" saved successfully!`);
            } else {
                alert('Error saving godown: ' + result.message);
            }
        } catch (error) {
            console.error('❌ Error adding godown:', error);
            alert('Error saving godown. Please try again.');
        } finally {
            if (saveGodownBtn) {
                saveGodownBtn.disabled = false;
                saveGodownBtn.textContent = 'Save New Godown';
            }
        }
    }

    // Attach click event to Save button
    if (saveGodownBtn) {
        console.log('✓ Attaching click handler to Save Godown button');
        saveGodownBtn.addEventListener('click', function(e) {
            console.log('🎯 BUTTON CLICKED - Direct event handler triggered');
            e.preventDefault();
            e.stopPropagation();
            saveNewGodown();
        });

        // Add additional click listener for debugging
        saveGodownBtn.onclick = function(e) {
            console.log('🎯 BUTTON CLICKED - onclick handler triggered');
        };

        // Show ready status
        const statusIndicator = document.getElementById('godownStatus');
        if (statusIndicator) {
            statusIndicator.style.display = 'block';
        }

        // Update debug info
        const debugText = document.getElementById('debugText');
        if (debugText) {
            debugText.textContent = `Script loaded ✓ | Button found ✓ | Click handler attached ✓ | Time: ${new Date().toLocaleTimeString()}`;
        }
    } else {
        console.error('❌ Cannot attach click handler - saveGodownBtn not found');

        // Show debug info
        const debugInfo = document.getElementById('debugInfo');
        const debugText = document.getElementById('debugText');
        if (debugInfo && debugText) {
            debugInfo.style.display = 'block';
            debugText.textContent = '❌ ERROR: saveGodownBtn not found! Button ID might be incorrect.';
        }
    }

    // Load godowns when page loads
    if (godownInput && godownDatalist) {
        console.log('✓ Godown elements found, loading godowns...');
        loadGodowns();
    } else {
        console.error('❌ Godown elements missing, skipping loadGodowns()');
    }
});

// Event delegation fallback - attach to document
document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'saveGodownBtn') {
        console.log('🎯 BUTTON CLICKED via event delegation');
        e.preventDefault();
        e.stopPropagation();

        // Call save function directly
        const godownInput = document.getElementById('paddy_unloading_godown');
        const godownDatalist = document.getElementById('godownList');
        const saveGodownBtn = document.getElementById('saveGodownBtn');

        if (!godownInput) {
            console.error('❌ godownInput not found');
            alert('Error: Godown input field not found');
            return;
        }

        const enteredValue = godownInput.value.trim();
        console.log('📝 Entered value:', enteredValue);

        if (!enteredValue) {
            alert('Please enter a godown name');
            return;
        }

        // Get current godowns
        let allGodowns = [];
        const existingOptions = godownDatalist ? godownDatalist.querySelectorAll('option') : [];
        existingOptions.forEach(opt => {
            if (opt.value) allGodowns.push({ name: opt.value });
        });

        // Check if exists
        const exists = allGodowns.some(g => g.name.toLowerCase() === enteredValue.toLowerCase());
        if (exists) {
            alert('This godown already exists in the list');
            return;
        }

        // Save to backend
        saveGodownBtn.disabled = true;
        saveGodownBtn.textContent = 'Saving...';

        fetch('/api/unloading-godowns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: enteredValue })
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(result => {
            console.log('Response data:', result);
            if (result.success) {
                // Update dropdown
                if (result.godowns && Array.isArray(result.godowns)) {
                    godownDatalist.innerHTML = '';
                    result.godowns.forEach(godown => {
                        const option = document.createElement('option');
                        option.value = godown.name;
                        godownDatalist.appendChild(option);
                    });
                }
                alert(`Godown "${enteredValue}" saved successfully!`);
            } else {
                alert('Error saving godown: ' + result.message);
            }
        })
        .catch(error => {
            console.error('❌ Error:', error);
            alert('Error saving godown. Please try again.');
        })
        .finally(() => {
            saveGodownBtn.disabled = false;
            saveGodownBtn.textContent = 'Save New Godown';
        });
    }
}, true); // Use capture phase

// ===== DYNAMIC INSTALMENT MANAGEMENT =====
let visibleInstalments = [1]; // Track which instalments are shown

function addInstalment() {
    // Find next hidden instalment
    for (let i = 2; i <= 5; i++) {
        if (!visibleInstalments.includes(i)) {
            const card = document.getElementById(`instalment_${i}_card`);
            if (card) {
                card.style.display = 'block';
                visibleInstalments.push(i);
            }
            break;
        }
    }

    // Hide add button if all 5 are visible
    if (visibleInstalments.length >= 5) {
        document.getElementById('addInstalmentBtn').style.display = 'none';
    }
}

function removeInstalment(num) {
    const card = document.getElementById(`instalment_${num}_card`);
    if (card) {
        card.style.display = 'none';

        // Clear all fields
        document.getElementById(`instalment_${num}_date`).value = '';
        document.getElementById(`instalment_${num}_amount`).value = '0';
        document.getElementById(`instalment_${num}_payment_method`).value = '';
        document.getElementById(`instalment_${num}_payment_bank_account`).value = '';
        document.getElementById(`instalment_${num}_comment`).value = '';

        // Remove from visible list
        visibleInstalments = visibleInstalments.filter(i => i !== num);

        // Show add button again
        document.getElementById('addInstalmentBtn').style.display = 'inline-block';
    }
}
