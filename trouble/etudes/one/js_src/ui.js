/**
 * @fileoverview UI logic for Etude One.
 * Fetches daily data and populates the Etude One app shell.
 */

// Note: The paths are relative to the final location in the 'docs' directory.
// We use absolute paths from the site root to ensure they resolve correctly.
import { getLatestEtudeData } from '/assets/js/core/data_fetcher.js';
import { setText, setHtml, updateStatusFooter } from '/assets/js/core/ui_updater.js';

// --- CONFIGURATION ---
// These should be replaced by your actual GitHub repo details.
// In a real app, this might be configured in the HTML or a global JS config file.
const REPO_OWNER = 'greple-test';
const REPO_NAME = 'test-1';
// ---------------------


/**
 * Renders the data for Etude One into the DOM.
 * @param {object} etudeOneData The specific data object for Etude One from the fetched JSON.
 */
function renderEtudeOne(etudeOneData) {
    if (!etudeOneData || !etudeOneData.data) {
        setHtml('dynamic-content-container', '<p class="placeholder">No daily data available for Etude One.</p>');
        return;
    }

    const { random_quote, sample_todo, static_info } = etudeOneData.data;

    let contentHtml = '<h3>Fetched Data:</h3><ul>';

    if (random_quote && random_quote.content) {
        contentHtml += `<li><strong>Random Quote:</strong> <em>"${random_quote.content}"</em> &mdash; ${random_quote.author}</li>`;
    } else {
        contentHtml += `<li><strong>Random Quote:</strong> Not available.</li>`;
    }

    if (sample_todo && sample_todo.title) {
        const completedStatus = sample_todo.completed ? 'Completed' : 'Not Completed';
        contentHtml += `<li><strong>Sample Todo:</strong> ${sample_todo.title} (Status: ${completedStatus})</li>`;
    } else {
        contentHtml += `<li><strong>Sample Todo:</strong> Not available.</li>`;
    }

    if (static_info && static_info.message) {
        contentHtml += `<li><strong>Static Info Message:</strong> ${static_info.message}</li>`;
    } else {
        contentHtml += `<li><strong>Static Info:</strong> Not available.</li>`;
    }

    contentHtml += '</ul>';

    setHtml('dynamic-content-container', contentHtml);
}


/**
 * Main function to orchestrate data fetching and rendering for Etude One.
 */
async function main() {
    updateStatusFooter('Fetching latest daily data...', 'loading');

    const result = await getLatestEtudeData(REPO_OWNER, REPO_NAME);

    if (result.status === 'success') {
        updateStatusFooter(`Successfully loaded data from release: ${result.version_tag}`, 'success');
        // Extract the data for this specific etude ('one')
        const etudeOneData = result.data?.one;
        renderEtudeOne(etudeOneData);
    } else {
        updateStatusFooter(`Error: ${result.message}`, 'error');
        setHtml('dynamic-content-container', `<p class="placeholder" style="color: red;">Could not load daily content. ${result.message}</p>`);
    }
}

// --- Entry Point ---
// Run the main function when the DOM is fully loaded.
document.addEventListener('DOMContentLoaded', main);
