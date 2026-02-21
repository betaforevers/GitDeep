const form = document.getElementById('analyze-form');
const urlInput = document.getElementById('repo-url');
const submitBtn = document.getElementById('submit-btn');
const statusMessage = document.getElementById('status-message');
const resultsSection = document.getElementById('results-section');
const logOutput = document.getElementById('log-output');

// Config
const API_BASE_URL = 'http://localhost:8000/api';
let activityChartInstance = null;
let intentChartInstance = null;

function addLog(message) {
    const p = document.createElement('p');
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    p.innerHTML = `<span style="color: #6b4cff">[${time}]</span> ${message}`;
    logOutput.appendChild(p);
    logOutput.scrollTop = logOutput.scrollHeight;
}

// Auto-analyze when a valid GitHub URL is pasted
urlInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/[^\/]+\/[^\/]+(\/)?$/i;

    // If input matches exactly (e.g. from a paste), auto-submit if not already analyzing
    if (githubRegex.test(val) && !submitBtn.disabled) {
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = urlInput.value.trim();
    if (!url) return;

    const languageSelect = document.getElementById('report-language');
    const language = languageSelect ? languageSelect.value : "English";

    // Reset UI
    submitBtn.disabled = true;
    submitBtn.textContent = 'Analyzing...';
    statusMessage.textContent = 'Connecting to backend...';
    statusMessage.className = 'status-message loading';
    resultsSection.classList.remove('hidden');
    document.getElementById('report-summary-box').style.display = 'none';
    document.getElementById('charts-grid').style.display = 'none';
    document.getElementById('download-btn').classList.add('hidden');

    // Reset Progress Bars
    document.getElementById('bar-stars').style.width = '0%';
    document.getElementById('bar-issues').style.width = '0%';
    document.getElementById('bar-bus-factor').style.width = '0%';
    document.getElementById('bar-stagnant').style.width = '0%';

    // Scroll back to top if they triggered this from below
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Show Premium Loading Animation
    logOutput.innerHTML = `
        <div class="loading-wrapper">
            <div class="spinner"></div>
            <div class="loading-text">Analyzing Repository Data...</div>
            <div class="loading-subtext">Fetching commits, issues, and running NLP reasoning</div>
        </div>
    `;

    addLog(`Initiating analysis for: ${url}`);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, language })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Analysis failed');
        }

        addLog(`Response received: ${data.message}`);

        if (data.details) {
            document.getElementById('result-title').textContent = `Analysis: ${data.details.stars > 0 ? 'Live' : 'Done'}`;
            document.getElementById('val-stars').textContent = data.details.stars.toLocaleString();
            document.getElementById('val-issues').textContent = data.details.open_issues.toLocaleString();
            document.getElementById('val-bus-factor').textContent = data.details.bus_factor;
            document.getElementById('val-stagnant').textContent = data.details.is_stagnant ? "Yes" : "No";

            // Animate Progress Bars (Max caps for visual scale)
            setTimeout(() => {
                const starsPx = Math.min((data.details.stars / 1000) * 100, 100);
                const issuesPx = Math.min((data.details.open_issues / 500) * 100, 100);
                const busFactorPx = Math.min((data.details.bus_factor / 10) * 100, 100);
                const stagnantPx = data.details.is_stagnant ? 100 : 0;

                document.getElementById('bar-stars').style.width = `${starsPx}%`;
                document.getElementById('bar-issues').style.width = `${issuesPx}%`;
                document.getElementById('bar-bus-factor').style.width = `${busFactorPx}%`;
                document.getElementById('bar-stagnant').style.width = `${stagnantPx}%`;
            }, 100);

            const badge = document.getElementById('result-badge');

            // Set based on status from Reason Engine
            if (data.status === "success") {
                if (data.health_score < 50) {
                    badge.textContent = "DEAD (Score: " + data.health_score + ")";
                    badge.className = "badge error";
                    badge.style.background = "rgba(255, 82, 82, 0.1)";
                    badge.style.color = "var(--danger)";
                    badge.style.borderColor = "rgba(255, 82, 82, 0.2)";
                } else if (data.health_score < 80) {
                    badge.textContent = "AT RISK (Score: " + data.health_score + ")";
                    badge.className = "badge active"; // Reuse general style, override color
                    badge.style.background = "rgba(255, 171, 64, 0.1)";
                    badge.style.color = "#ffab40";
                    badge.style.borderColor = "rgba(255, 171, 64, 0.2)";
                } else {
                    badge.textContent = "ACTIVE (Score: " + data.health_score + ")";
                    badge.className = "badge active";
                    badge.style.background = "rgba(0, 230, 118, 0.1)";
                    badge.style.color = "var(--success)";
                    badge.style.borderColor = "rgba(0, 230, 118, 0.2)";
                }
            }

            // Display Report Summary
            const summaryBox = document.getElementById('report-summary-box');
            const summaryText = document.getElementById('report-summary-text');
            const downloadBtn = document.getElementById('download-btn');

            summaryText.textContent = data.message;
            summaryBox.style.display = 'block';

            if (data.pdf_url) {
                downloadBtn.href = data.pdf_url;
                downloadBtn.classList.remove('hidden');
                addLog(`Generated detailed reasoning PDF report. Ready for download.`);
            }

            // Draw Charts
            if (data.chart_data) {
                document.getElementById('charts-grid').style.display = 'grid';
                drawCharts(data.chart_data.activity_trend, data.chart_data.intent_breakdown);
                addLog(`Rendered interactive live charts.`);
            }

            addLog(`Calculated health metrics: Analyzed ${data.details.commits_analyzed} recent commits.`);
        }

        statusMessage.textContent = 'Analysis complete!';
        statusMessage.className = 'status-message success';

        // Smooth scroll to results
        setTimeout(() => {
            document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);

    } catch (error) {
        console.error('Error:', error);
        statusMessage.textContent = error.message;
        statusMessage.className = 'status-message error';
        addLog(`<span style="color: #ff5252">Error: ${error.message}</span>`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Analyze Repo';
    }
});

// History Carousel Logic
document.addEventListener('DOMContentLoaded', loadHistory);

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);
        if (!response.ok) return;

        const data = await response.json();
        const historyData = data.history || [];

        if (historyData.length === 0) return;

        const section = document.getElementById('history-section');
        const track = document.getElementById('history-track');

        track.innerHTML = ''; // Clear skeleton

        historyData.forEach(item => {
            const date = new Date(item.analyzed_at).toLocaleDateString();
            const isHealthy = item.score >= 80;
            const isWarning = item.score >= 50 && item.score < 80;
            let statusColor = 'var(--danger)';
            if (isHealthy) statusColor = 'var(--success)';
            if (isWarning) statusColor = '#ffab40';

            const card = document.createElement('div');
            card.className = 'history-card';
            card.innerHTML = `
                <div>
                    <div class="history-card-header">
                        <span class="history-repo-name">${item.repo_name}</span>
                        <span class="badge" style="background: ${statusColor}22; color: ${statusColor}; border: 1px solid ${statusColor}44;">
                            ${item.score}/100
                        </span>
                    </div>
                    <div class="history-summary">${item.summary}</div>
                </div>
                <div class="history-card-footer">
                    <span class="history-date">${date}</span>
                    <div style="display: flex; gap: 10px;">
                        ${item.pdf_url ? `<a href="${item.pdf_url}" target="_blank" class="history-download-btn" aria-label="Download PDF" style="color: #6b4cff; display: flex; align-items: center; gap: 4px; text-decoration: none;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg> PDF
                        </a>` : ''}
                        <a href="#" class="history-view-btn" data-repo="https://github.com/${item.repo_name}" style="color: var(--accent); text-decoration: none; display: flex; align-items: center;">View &rarr;</a>
                    </div>
                </div>
            `;
            track.appendChild(card);
        });

        section.style.display = 'block'; // Reveal

        // Add event listener for the View buttons
        track.addEventListener('click', (e) => {
            if (e.target.classList.contains('history-view-btn')) {
                e.preventDefault();
                const repoUrl = e.target.getAttribute('data-repo');
                urlInput.value = repoUrl;
                if (!submitBtn.disabled) {
                    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }
            }
        });

    } catch (e) {
        console.error("Failed to fetch history:", e);
    }
}

function drawCharts(activityTrend, intentBreakdown) {
    Chart.defaults.color = '#888888';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    // Destroy previous instances if any
    if (activityChartInstance) activityChartInstance.destroy();
    if (intentChartInstance) intentChartInstance.destroy();

    // 1. Activity Linear Chart
    const ctxActivity = document.getElementById('activityChart').getContext('2d');

    // Gradient for line chart
    const gradient = ctxActivity.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(107, 76, 255, 0.5)');
    gradient.addColorStop(1, 'rgba(107, 76, 255, 0.0)');

    activityChartInstance = new Chart(ctxActivity, {
        type: 'line',
        data: {
            labels: Object.keys(activityTrend || {}),
            datasets: [{
                label: 'Commit Activity',
                data: Object.values(activityTrend || {}),
                borderColor: '#6b4cff',
                backgroundColor: gradient,
                borderWidth: 2,
                pointBackgroundColor: '#00e676',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#00e676',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: 'Commit Activity Trend', color: '#f0f0f0', font: { size: 16 } },
                legend: { display: false }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true }
            }
        }
    });

    // 2. Intent Pie Chart
    const ctxIntent = document.getElementById('intentChart').getContext('2d');

    let labels = Object.keys(intentBreakdown || {});
    let sizes = Object.values(intentBreakdown || {});

    // Filter out 0 size slices
    const filteredLabels = [];
    const filteredSizes = [];
    for (let i = 0; i < sizes.length; i++) {
        if (sizes[i] > 0) {
            filteredLabels.push(labels[i]);
            filteredSizes.push(sizes[i]);
        }
    }

    if (filteredSizes.length === 0) {
        filteredLabels.push("Unknown");
        filteredSizes.push(1);
    }

    intentChartInstance = new Chart(ctxIntent, {
        type: 'doughnut',
        data: {
            labels: filteredLabels,
            datasets: [{
                data: filteredSizes,
                backgroundColor: ['#00e676', '#ff5252', '#ffab40', '#42a5f5', '#9e9e9e'],
                borderColor: 'transparent',
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                title: { display: true, text: 'Development Focus (Semantic)', color: '#f0f0f0', font: { size: 16 } },
                legend: { position: 'bottom', labels: { padding: 20 } }
            }
        }
    });
}
