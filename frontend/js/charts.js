let activityChartInstance = null;
let intentChartInstance = null;

export function drawCharts(activityTrend, intentBreakdown) {
    if (typeof Chart === 'undefined') {
        console.warn("Chart.js is not loaded.");
        return;
    }

    Chart.defaults.color = '#888888';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    if (activityChartInstance) activityChartInstance.destroy();
    if (intentChartInstance) intentChartInstance.destroy();

    const ctxActivity = document.getElementById('activityChart').getContext('2d');
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

    const ctxIntent = document.getElementById('intentChart').getContext('2d');
    let labels = Object.keys(intentBreakdown || {});
    let sizes = Object.values(intentBreakdown || {});

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
