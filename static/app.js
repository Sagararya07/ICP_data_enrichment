document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileDetails = document.getElementById('fileDetails');
    const fileNameDisplay = document.getElementById('fileName');
    const removeFileBtn = document.getElementById('removeFileBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    
    const runEnrichmentBtn = document.getElementById('runEnrichmentBtn');
    const engineStatus = document.getElementById('engineStatus');
    const pendingCount = document.getElementById('pendingCount');
    const enrichedCount = document.getElementById('enrichedCount');
    const eligibleCount = document.getElementById('eligibleCount');
    const strongFitCount = document.getElementById('strongFitCount');
    const potentialFitCount = document.getElementById('potentialFitCount');
    const notFitCount = document.getElementById('notFitCount');
    const failedCount = document.getElementById('failedCount');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');

    const exportEligibleBtn = document.getElementById('exportEligibleBtn');
    const exportStrongBtn = document.getElementById('exportStrongBtn');
    const exportPotentialBtn = document.getElementById('exportPotentialBtn');
    const exportAllBtn = document.getElementById('exportAllBtn');

    let selectedFile = null;
    let pollInterval = null;

    // Fetch initial status on load
    fetchStatus();

    // --- Drag & Drop Logic ---
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            handleFileSelect(this.files[0]);
        }
    });

    function handleFileSelect(file) {
        const isCsv = file.type === 'text/csv' || file.name.endsWith('.csv');
        const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                        file.type === 'application/vnd.ms-excel' ||
                        file.name.endsWith('.xlsx') || file.name.endsWith('.xls');

        if (!isCsv && !isExcel) {
            showStatus(uploadStatus, 'Please upload a valid CSV or Excel file.', 'error');
            return;
        }
        
        selectedFile = file;
        fileNameDisplay.textContent = file.name;
        dropZone.style.display = 'none';
        fileDetails.style.display = 'flex';
        uploadBtn.disabled = false;
        showStatus(uploadStatus, '', '');
    }

    removeFileBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        dropZone.style.display = 'block';
        fileDetails.style.display = 'none';
        uploadBtn.disabled = true;
    });

    // --- Upload Logic ---
    uploadBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('file', selectedFile);

        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading...';
        showStatus(uploadStatus, 'Processing and inserting records into database...', 'info');

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                showStatus(uploadStatus, `<i class="fa-solid fa-check"></i> ${result.message}`, 'success');
                removeFileBtn.click(); // Reset upload UI
                fetchStatus(); // Update counts
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            showStatus(uploadStatus, `<i class="fa-solid fa-circle-exclamation"></i> ${error.message}`, 'error');
        } finally {
            uploadBtn.innerHTML = 'Upload to Database';
        }
    });

    // --- Enrichment Engine Logic ---
    runEnrichmentBtn.addEventListener('click', async () => {
        runEnrichmentBtn.disabled = true;
        runEnrichmentBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Engine Running...';
        showStatus(engineStatus, 'Enrichment engine started in background.', 'info');

        try {
            const response = await fetch('/api/enrich', { method: 'POST' });
            const result = await response.json();
            
            if (response.ok) {
                // Start polling status
                if (!pollInterval) {
                    pollInterval = setInterval(fetchStatus, 3000);
                }
            } else {
                throw new Error(result.detail || 'Failed to start engine');
            }
        } catch (error) {
            showStatus(engineStatus, `<i class="fa-solid fa-circle-exclamation"></i> ${error.message}`, 'error');
            runEnrichmentBtn.disabled = false;
            runEnrichmentBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Enrichment';
        }
    });

    // --- Status Polling Logic ---
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (!response.ok) {
                console.error("Status endpoint error:", data.detail);
                return;
            }
            
            const total = data.total || 0;
            const enriched = data.enriched || 0;
            const failed = data.failed || 0;
            const eligible = data.eligible_companies || 0;
            const strongFits = data.strong_fits || 0;
            const potentialFits = data.potential_fits || 0;
            const notFits = data.not_fits || 0;
            const pending = total - enriched - failed;

            pendingCount.textContent = pending;
            enrichedCount.textContent = enriched;
            eligibleCount.textContent = eligible;
            strongFitCount.textContent = strongFits;
            potentialFitCount.textContent = potentialFits;
            notFitCount.textContent = notFits;
            failedCount.textContent = failed;

            let percentage = 0;
            if (total > 0) {
                percentage = Math.round(((enriched + failed) / total) * 100);
            }
            
            progressBar.style.width = `${percentage}%`;
            progressPercent.textContent = `${percentage}%`;

            // If a run was active and finishes
            if (pollInterval && pending === 0) {
                clearInterval(pollInterval);
                pollInterval = null;
                runEnrichmentBtn.disabled = false;
                runEnrichmentBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Enrichment';
                showStatus(engineStatus, `<i class="fa-solid fa-check-double"></i> Enrichment complete!`, 'success');
            }
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }

    // Helper
    function showStatus(element, message, type) {
        element.innerHTML = message;
        element.className = `status-msg ${type}`;
    }

    // --- Export Logic ---
    function triggerExport(fitStatus) {
        let url = '/api/export';
        if (fitStatus) {
            url += `?fit_status=${encodeURIComponent(fitStatus)}`;
        }
        window.location.href = url;
    }

    exportEligibleBtn.addEventListener('click', () => triggerExport('Eligible Company'));
    exportStrongBtn.addEventListener('click', () => triggerExport('Strong Fit'));
    exportPotentialBtn.addEventListener('click', () => triggerExport('Potential Fit'));
    exportAllBtn.addEventListener('click', () => triggerExport('All'));
});
