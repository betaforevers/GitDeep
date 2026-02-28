import { analyzeRepository, getHistory } from './api.js';
import { elements, addLog, resetUI, displayResults, displayError, restoreUIState, renderHistory } from './ui.js';

async function handleAnalyze(url) {
    if (!url) return;

    resetUI();
    addLog(`Initiating analysis for: ${url}`);

    try {
        const data = await analyzeRepository(url, (msg) => {
            addLog(`Status Update: ${msg}`);
        });

        // Polling returns the result object directly on success.
        // We will mock the 'status' and 'message' to fit displayResults structure
        addLog(`Response received: Analysis complete`);

        if (data) {
            displayResults({ "status": "success", "message": "Analysis Complete", "details": data.details, "chart_data": data.chart_data, "pdf_url": data.pdf_url, "health_score": data.health_score });
        }
    } catch (error) {
        console.error('Error:', error);
        displayError(error);
    } finally {
        restoreUIState();
    }
}

elements.form.addEventListener('submit', (e) => {
    e.preventDefault();
    const url = elements.urlInput.value.trim();
    handleAnalyze(url);
});

async function loadHistory() {
    try {
        console.log("Fetching history from API...");
        const data = await getHistory();
        const historyData = data.history || [];
        console.log(`Fetched ${historyData.length} history items.`);

        if (historyData.length === 0) return;

        renderHistory(historyData, (repoUrl) => {
            elements.urlInput.value = repoUrl;
            if (!elements.submitBtn.disabled) {
                // Simulate form submission visually
                handleAnalyze(repoUrl);
            }
        });

    } catch (e) {
        console.error("Failed to fetch history:", e);
    }
}

document.addEventListener('DOMContentLoaded', loadHistory);
