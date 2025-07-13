/**
 * @fileoverview UI logic for Etude Zero.
 * Fetches daily data and populates the Etude Zero app shell, focusing on
 * displaying the status of all other etudes.
 */

import { getLatestEtudeData } from '/assets/js/core/data_fetcher.js';
import { setHtml, updateStatusFooter } from '/assets/js/core/ui_updater.js';

// --- CONFIGURATION ---
const REPO_OWNER = 'greple-test';
const REPO_NAME = 'test-1';
// ---------------------

/**
 * Fetches the Mustache template for Etude Zero's status table.
 * @returns {Promise<string>} The template string.
 */
async function getTemplate() {
    // Use an absolute path from the site root to fetch the template
    const response = await fetch('/assets/js/zero/templates/status_table.mustache');
    if (!response.ok) {
        throw new Error('Failed to fetch status_table.mustache template');
    }
    return response.text();
}

/**
 * Renders the daily status of all etudes into a table using a Mustache template.
 * @param {string} template The Mustache template string.
 * @param {object} allEtudesData The full data object from the fetched JSON.
 */
function renderAllEtudesStatus(template, allEtudesData) {
    if (!allEtudesData || Object.keys(allEtudesData).length === 0) {
        setHtml('daily-status-container', '<p class="placeholder">No daily status data found.</p>');
        return;
    }

    // Prepare data for Mustache: transform the object into an array of objects
    const view_data = {
        etudes: Object.keys(allEtudesData).map(key => ({
            name: key,
            status: allEtudesData[key].status || 'UNKNOWN',
            status_class: (allEtudesData[key].status || 'unknown').toLowerCase(),
            actions_log: allEtudesData[key].actions_log
        })).sort((a, b) => { // Sort the array for consistent rendering
            if (a.name === 'zero') return -1;
            if (b.name === 'zero') return 1;
            return a.name.localeCompare(b.name);
        })
    };

    const renderedHtml = window.Mustache.render(template, view_data);
    setHtml('daily-status-container', renderedHtml);
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
    updateStatusFooter('Fetching latest daily data and template...', 'loading');

    try {
        const [template, result] = await Promise.all([
            getTemplate(),
            getLatestEtudeData(REPO_OWNER, REPO_NAME)
        ]);

        if (result.status === 'success') {
            updateStatusFooter(`Successfully loaded data from release: ${result.version_tag}`, 'success');
            renderAllEtudesStatus(template, result.data);
        } else if (result.status === 'not_found') {
            updateStatusFooter('No recent data found.', 'warning');
            setHtml('daily-status-container', `<p class="placeholder">No recent daily status data could be found. Please check back later.</p>`);
        } else { // 'error'
            updateStatusFooter(`Error: ${result.message}`, 'error');
            setHtml('daily-status-container', `<p class="placeholder" style="color: red;">Could not load daily status overview. ${result.message}</p>`);
        }
    } catch (error) {
        console.error("Failed to initialize Etude Zero:", error);
        updateStatusFooter(`Error: ${error.message}`, 'error');
        setHtml('daily-status-container', `<p class="placeholder" style="color: red;">An unexpected error occurred during initialization.</p>`);
    }
}

// --- Entry Point ---
document.addEventListener('DOMContentLoaded', main);
