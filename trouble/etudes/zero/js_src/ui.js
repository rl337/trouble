/**
 * @fileoverview UI logic for Etude Zero.
 * Fetches daily data and populates the Etude Zero app shell, focusing on
 * displaying the status of all other etudes.
 */

import { getLatestEtudeData } from '/assets/js/core/data_fetcher.js';
import { setText, setHtml, updateStatusFooter } from '/assets/js/core/ui_updater.js';

// --- CONFIGURATION ---
const REPO_OWNER = 'greple-test';
const REPO_NAME = 'test-1';
// ---------------------

/**
 * Renders the daily status of all etudes into a table.
 * @param {object} allEtudesData The full data object from the fetched JSON.
 */
function renderAllEtudesStatus(allEtudesData) {
    if (!allEtudesData || Object.keys(allEtudesData).length === 0) {
        setHtml('daily-status-container', '<p class="placeholder">No daily status data found.</p>');
        return;
    }

    let tableHtml = `
        <table>
            <thead>
                <tr>
                    <th>Etude Name</th>
                    <th>Daily Status</th>
                    <th>Actions Log</th>
                </tr>
            </thead>
            <tbody>
    `;

    // Sort etudes: 'zero' first, then alphabetically
    const etudeNames = Object.keys(allEtudesData).sort((a, b) => {
        if (a === 'zero') return -1;
        if (b === 'zero') return 1;
        return a.localeCompare(b);
    });

    for (const etudeName of etudeNames) {
        const etudeResult = allEtudesData[etudeName];
        if (!etudeResult) continue;

        const status = etudeResult.status || 'UNKNOWN';
        const actionsLog = etudeResult.actions_log || ['No actions logged.'];

        // Format actions log into a list
        const logHtml = '<ul>' + actionsLog.map(log => `<li>${escapeHtml(log)}</li>`).join('') + '</ul>';

        tableHtml += `
            <tr>
                <td><strong>${escapeHtml(etudeName)}</strong></td>
                <td><span class="status-${status.toLowerCase()}">${escapeHtml(status)}</span></td>
                <td>${logHtml}</td>
            </tr>
        `;
    }

    tableHtml += `
            </tbody>
        </table>
    `;

    setHtml('daily-status-container', tableHtml);
}

/**
 * A simple utility to escape HTML to prevent XSS.
 * @param {string} unsafe The string to escape.
 * @returns {string} The escaped string.
 */
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}


/**
 * Main function to orchestrate data fetching and rendering for Etude Zero.
 */
async function main() {
    updateStatusFooter('Fetching latest daily data...', 'loading');

    const result = await getLatestEtudeData(REPO_OWNER, REPO_NAME);

    if (result.status === 'success') {
        updateStatusFooter(`Successfully loaded data from release: ${result.version_tag}`, 'success');
        renderAllEtudesStatus(result.data);
    } else if (result.status === 'not_found') {
        updateStatusFooter('No recent data found.', 'warning');
        setHtml('daily-status-container', `<p class="placeholder">No recent daily status data could be found. Please check back later.</p>`);
    } else { // 'error'
        updateStatusFooter(`Error: ${result.message}`, 'error');
        setHtml('daily-status-container', `<p class="placeholder" style="color: red;">Could not load daily status overview. ${result.message}</p>`);
    }
}

// --- Entry Point ---
document.addEventListener('DOMContentLoaded', main);
