// src/api.js

import axios from 'axios';

const API_BASE = 'http://localhost:5000';

export async function fetchUnlabeledData(limit = 200) {
    try {
        const response = await axios.get(`${API_BASE}/get_unlabeled`, {
            params: { limit }
        });
        return response.data.sensor_data;
    } catch (error) {
        console.error("Fehler beim Abrufen der Daten:", error);
        return [];
    }
}

export async function labelData(id, label) {
    try {
        const response = await axios.post(`${API_BASE}/label_data`, { id, label });
        return response.data;
    } catch (error) {
        console.error("Fehler beim Labeln der Daten:", error);
        throw error;
    }
}

export async function batchLabel(ids, label) {
    try {
        const response = await axios.post(`${API_BASE}/batch_label`, { ids, label });
        return response.data;
    } catch (error) {
        console.error("Fehler beim Batch-Labeln der Daten:", error);
        throw error;
    }
}
