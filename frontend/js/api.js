const API_BASE_URL = 'http://localhost:8000/api';

export async function analyzeRepository(url) {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed');
    }

    return data;
}

export async function getHistory() {
    const response = await fetch(`${API_BASE_URL}/history`);
    if (!response.ok) {
        throw new Error(`History API returned error ${response.status}`);
    }
    return await response.json();
}
