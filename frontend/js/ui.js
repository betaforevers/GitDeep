import { drawCharts } from './charts.js';

export const elements = {
    form: document.getElementById('analyze-form'),
    urlInput: document.getElementById('repo-url'),
    submitBtn: document.getElementById('submit-btn'),
    statusMessage: document.getElementById('status-message'),
    resultsSection: document.getElementById('results-section'),
    logOutput: document.getElementById('log-output'),
    summaryBox: document.getElementById('report-summary-box'),
    chartsGrid: document.getElementById('charts-grid'),
    fileHealthSection: document.getElementById('file-health-section'),
    downloadBtn: document.getElementById('download-btn'),
    historySection: document.getElementById('history-section'),
    historyTrack: document.getElementById('history-track')
};

export function addLog(message) {
    const p = document.createElement('p');
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    p.innerHTML = `<span style="color: #6b4cff">[${time}]</span> ${message}`;
    elements.logOutput.appendChild(p);
    elements.logOutput.scrollTop = elements.logOutput.scrollHeight;
}

export function resetUI() {
    elements.submitBtn.disabled = true;
    elements.submitBtn.textContent = 'Analyzing...';
    elements.statusMessage.textContent = 'Connecting to backend...';
    elements.statusMessage.className = 'status-message loading';
    elements.resultsSection.classList.remove('hidden');
    elements.summaryBox.style.display = 'none';
    elements.chartsGrid.style.display = 'none';
    elements.fileHealthSection.style.display = 'none';
    elements.downloadBtn.classList.add('hidden');

    document.getElementById('bar-stars').style.width = '0%';
    document.getElementById('bar-issues').style.width = '0%';
    document.getElementById('bar-bus-factor').style.width = '0%';
    document.getElementById('bar-stagnant').style.width = '0%';
<<<<<<< HEAD
    document.getElementById('bar-quality').style.width = '0%';
    document.getElementById('bar-plagiarism').style.width = '0%';
=======
>>>>>>> bde3534b1529b1c615e6852836f6d32d6cef0f99

    window.scrollTo({ top: 0, behavior: 'smooth' });

    elements.logOutput.innerHTML = `
        <div class="loading-wrapper">
            <div class="spinner"></div>
            <div class="loading-text">Analyzing Repository Data...</div>
            <div class="loading-subtext">Fetching commits, issues, and running NLP reasoning</div>
        </div>
    `;
}

export function displayResults(data) {
    document.getElementById('result-title').textContent = `Analysis: ${data.details.stars > 0 ? 'Live' : 'Done'}`;
    document.getElementById('val-stars').textContent = data.details.stars.toLocaleString();
    document.getElementById('val-issues').textContent = data.details.open_issues.toLocaleString();
    document.getElementById('val-bus-factor').textContent = data.details.bus_factor;
    document.getElementById('val-stagnant').textContent = data.details.is_stagnant ? "Yes" : "No";

<<<<<<< HEAD
    // Add quality and plagiarism logic
    const qualityLabel = data.details.code_quality ? data.details.code_quality.sqale_rating : "--";
    document.getElementById('val-quality').textContent = qualityLabel;

    // Convert 0-1 plagiarism ratio to percentage string
    let plagiarismPct = 0;
    if (data.details.plagiarism && data.details.plagiarism.internal_duplication_pct !== undefined) {
        plagiarismPct = Math.round(data.details.plagiarism.internal_duplication_pct * 100);
    }
    document.getElementById('val-plagiarism').textContent = `${plagiarismPct}%`;

=======
>>>>>>> bde3534b1529b1c615e6852836f6d32d6cef0f99
    setTimeout(() => {
        const starsPx = Math.min((data.details.stars / 1000) * 100, 100);
        const issuesPx = Math.min((data.details.open_issues / 500) * 100, 100);
        const busFactorPx = Math.min((data.details.bus_factor / 10) * 100, 100);
        const stagnantPx = data.details.is_stagnant ? 100 : 0;

<<<<<<< HEAD
        // Let's create visual widths for the new metrics
        let qualityPx = 0;
        if (qualityLabel === 'A') qualityPx = 100;
        else if (qualityLabel === 'B') qualityPx = 60;
        else if (qualityLabel === 'C') qualityPx = 30;

        const plagiarismPx = Math.min(plagiarismPct, 100);

=======
>>>>>>> bde3534b1529b1c615e6852836f6d32d6cef0f99
        document.getElementById('bar-stars').style.width = `${starsPx}%`;
        document.getElementById('bar-issues').style.width = `${issuesPx}%`;
        document.getElementById('bar-bus-factor').style.width = `${busFactorPx}%`;
        document.getElementById('bar-stagnant').style.width = `${stagnantPx}%`;
<<<<<<< HEAD
        document.getElementById('bar-quality').style.width = `${qualityPx}%`;
        document.getElementById('bar-plagiarism').style.width = `${plagiarismPx}%`;
=======
>>>>>>> bde3534b1529b1c615e6852836f6d32d6cef0f99
    }, 100);

    updateBadge(data);
    displayFileMetrics(data.details.file_metrics);
    displaySummary(data);

    if (data.chart_data) {
        elements.chartsGrid.style.display = 'grid';
        drawCharts(data.chart_data.activity_trend, data.chart_data.intent_breakdown);
        addLog(`Rendered interactive live charts.`);
    }

    addLog(`Calculated health metrics: Analyzed ${data.details.commits_analyzed} recent commits.`);

    elements.statusMessage.textContent = 'Analysis complete!';
    elements.statusMessage.className = 'status-message success';

    setTimeout(() => {
        elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

function updateBadge(data) {
    const badge = document.getElementById('result-badge');
    if (data.status === "success") {
        if (data.health_score < 50) {
            badge.textContent = "DEAD (Score: " + data.health_score + ")";
            badge.className = "badge error";
            badge.style.background = "rgba(255, 82, 82, 0.1)";
            badge.style.color = "var(--danger)";
            badge.style.borderColor = "rgba(255, 82, 82, 0.2)";
        } else if (data.health_score < 80) {
            badge.textContent = "AT RISK (Score: " + data.health_score + ")";
            badge.className = "badge active";
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
}

function displayFileMetrics(fileMetrics) {
    if (fileMetrics && fileMetrics.total_files_tracked > 0) {
        elements.fileHealthSection.style.display = 'block';

        renderList('list-bug-prone', fileMetrics.bug_prone, (i) => `(${i.commit_count} commits)`);
        renderList('list-hotspots', fileMetrics.hotspots, (i) => `(${i.changes} changes)`);
        renderList('list-legacy', fileMetrics.legacy_candidates, (i) => `(${i.age_days} days dormant)`);
    }
}

function renderList(elementId, items, formatStrFn) {
    const ul = document.getElementById(elementId);
    ul.innerHTML = '';
    if (!items || items.length === 0) {
        ul.innerHTML = '<li style="opacity: 0.5;">None detected</li>';
        return;
    }
    items.forEach(item => {
        const li = document.createElement('li');
        li.style.marginBottom = '4px';
        li.style.whiteSpace = 'nowrap';
        li.style.overflow = 'hidden';
        li.style.textOverflow = 'ellipsis';
        let shortName = item.filename;
        if (shortName.length > 40) {
            shortName = "..." + shortName.substring(shortName.length - 37);
        }
        li.innerHTML = `<span style="color: #fff;" title="${item.filename}">${shortName}</span> <span style="opacity: 0.7;">${formatStrFn(item)}</span>`;
        ul.appendChild(li);
    });
}

function displaySummary(data) {
    const summaryText = document.getElementById('report-summary-text');
    summaryText.textContent = data.message;
    elements.summaryBox.style.display = 'block';

    if (data.pdf_url) {
        elements.downloadBtn.href = data.pdf_url;
        elements.downloadBtn.classList.remove('hidden');
        addLog(`Generated detailed reasoning PDF report. Ready for download.`);
    }
}

export function displayError(error) {
<<<<<<< HEAD
    elements.logOutput.innerHTML = '';
=======
>>>>>>> bde3534b1529b1c615e6852836f6d32d6cef0f99
    elements.statusMessage.textContent = error.message;
    elements.statusMessage.className = 'status-message error';
    addLog(`<span style="color: #ff5252">Error: ${error.message}</span>`);
}

export function restoreUIState() {
    elements.submitBtn.disabled = false;
    elements.submitBtn.textContent = 'Analyze Repo';
}

export function renderHistory(historyData, onHistoryItemClick) {
    elements.historyTrack.innerHTML = '';

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
        elements.historyTrack.appendChild(card);
    });

    elements.historySection.style.display = 'block';

    elements.historyTrack.addEventListener('click', (e) => {
        if (e.target.classList.contains('history-view-btn')) {
            e.preventDefault();
            const repoUrl = e.target.getAttribute('data-repo');
            onHistoryItemClick(repoUrl);
        }
    });
}
