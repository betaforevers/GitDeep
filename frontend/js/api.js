<<<<<<< HEAD
// Determine API URL based on environment (Docker vs Local)
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? `http://${window.location.hostname}:8000/api`
    : '/api'; // fallback for production

export async function analyzeRepository(url, onProgress) {
    // 1. Start the task
=======
const API_BASE_URL = 'http://localhost:8000/api';

export async function analyzeRepository(url) {
>>>>>>> bde3534b1529b1c615e6852836f6d32d6cef0f99
    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
    });

    const data = await response.json();

    if (!response.ok) {
<<<<<<< HEAD
        throw new Error(data.detail || 'Analysis failed to start');
    }

    // If it was cached, return the result immediately
    if (data.task_id === 'cached') {
        return data.result;
    }

    // 2. Poll for results 
    const taskId = data.task_id;
    return await pollTaskStatus(taskId, onProgress);
}

async function pollTaskStatus(taskId, onProgress) {
    const maxRetries = 60; // 60 * 5s = 5 minutes timeout
    let retries = 0;

    while (retries < maxRetries) {
        const response = await fetch(`${API_BASE_URL}/analyze/${taskId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Polling failed');
        }

        if (data.status === 'success') {
            return data.result;
        } else if (data.status === 'failed') {
            throw new Error(data.message || 'Analysis failed during processing');
        } else {
            // Pending or Processing
            if (onProgress && data.message) {
                onProgress(data.message);
            }
        }

        // Wait 5 seconds before polling again
        await new Promise(r => setTimeout(r, 5000));
        retries++;
    }

    throw new Error('Analysis timed out after 5 minutes.');
=======
        throw new Error(data.detail || 'Analysis failed');
    }

    return data;
>>>>>>> bde3534b1529b1c615e6852836f6d32d6cef0f99
}

export async function getHistory() {
    const response = await fetch(`${API_BASE_URL}/history`);
    if (!response.ok) {
        throw new Error(`History API returned error ${response.status}`);
    }
    return await response.json();
}
