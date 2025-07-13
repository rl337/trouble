/**
 * @fileoverview UI logic for Etude One.
 * Fetches daily data and populates the Etude One app shell.
 */

// Note: The paths are relative to the final location in the 'docs' directory.
// We use absolute paths from the site root to ensure they resolve correctly.
import { getLatestEtudeData } from '/assets/js/core/data_fetcher.js';
import { setHtml, updateStatusFooter } from '/assets/js/core/ui_updater.js';

// --- CONFIGURATION ---
// These should be replaced by your actual GitHub repo details.
// In a real app, this might be configured in the HTML or a global JS config file.
const REPO_OWNER = 'greple-test';
const REPO_NAME = 'test-1';
// ---------------------


/**
 * Fetches the Mustache template for Etude One's content.
 * @returns {Promise<string>} The template string.
 */
async function getTemplate() {
    // Use an absolute path from the site root to fetch the template
    const response = await fetch('/assets/js/one/templates/content.mustache');
    if (!response.ok) {
        throw new Error('Failed to fetch content.mustache template');
    }
    return response.text();
}

/**
 * Renders the data for Etude One into the DOM using a Mustache template.
 * @param {string} template The Mustache template string.
 * @param {object} etudeOneData The specific data object for Etude One from the fetched JSON.
 */
function renderEtudeOne(template, etudeOneData) {
    if (!etudeOneData || !etudeOneData.data) {
        setHtml('dynamic-content-container', '<p class="placeholder">No daily data available for Etude One.</p>');
        return;
    }

    // The data object passed to Mustache should match the template's variable names.
    // The template uses sections like {{#random_quote}} so we can pass the data object directly.
    const renderedHtml = window.Mustache.render(template, etudeOneData.data);
    setHtml('dynamic-content-container', renderedHtml);
}


/**
 * Main function to orchestrate data fetching and rendering for Etude One.
 */
async function main() {
    updateStatusFooter('Fetching latest daily data and template...', 'loading');

    try {
        // Fetch template and data in parallel for efficiency
        const [template, result] = await Promise.all([
            getTemplate(),
            getLatestEtudeData(REPO_OWNER, REPO_NAME)
        ]);

        if (result.status === 'success') {
            updateStatusFooter(`Successfully loaded data from release: ${result.version_tag}`, 'success');
            const etudeOneData = result.data?.one;
            renderEtudeOne(template, etudeOneData);
        } else if (result.status === 'not_found') {
            updateStatusFooter('No recent data found.', 'warning');
            setHtml('dynamic-content-container', `<p class="placeholder">No recent daily data could be found. Please check back later.</p>`);
        } else { // 'error'
            updateStatusFooter(`Error: ${result.message}`, 'error');
            setHtml('dynamic-content-container', `<p class="placeholder" style="color: red;">Could not load daily content. ${result.message}</p>`);
        }
    } catch (error) {
        console.error("Failed to initialize Etude One:", error);
        updateStatusFooter(`Error: ${error.message}`, 'error');
        setHtml('dynamic-content-container', `<p class="placeholder" style="color: red;">An unexpected error occurred during initialization.</p>`);
    }
}

// --- Entry Point ---
// Run the main function when the DOM is fully loaded.
document.addEventListener('DOMContentLoaded', main);
