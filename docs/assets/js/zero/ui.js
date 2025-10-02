/**
 * @fileoverview UI logic for Etude Zero.
 * Fetches daily data and populates the Etude Zero app shell, focusing on
 * displaying the status of all other etudes.
 */

import { getLatestEtudeData } from '../core/data_fetcher.js';
import { setHtml, updateStatusFooter } from '../core/ui_updater.js';
import { SkinContextFactory, SkinManager } from '../core/skin_manager.js';
import { shadeDay, shadeNight } from '../../skins/shade.js';
import { sunMorning, sunAfternoon, sunEvening, sunNight } from '../../skins/sun.js';
import { defaultSkin } from '../../skins/default.js';

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
    const response = await fetch('../assets/js/zero/templates/status_table.mustache');
    if (!response.ok) {
        throw new Error('Failed to fetch status_table.mustache template');
    }
    return response.text();
}

/**
 * Renders the daily status of all etudes into a table using a Mustache template.
 * @param {string} template The Mustache template string.
 * @param {object} allEtudesData The full data object from the fetched JSON.
 * @param {object} skin The selected skin object.
 */
function renderAllEtudesStatus(template, allEtudesData, skin) {
    if (!allEtudesData || Object.keys(allEtudesData).length === 0) {
        setHtml('daily-status-container', '<p class="placeholder">No daily status data found.</p>');
        return;
    }

    // Prepare data for Mustache: transform the object into an array of objects
    const view_data = {
        etudes: Object.keys(allEtudesData).map(key => {
            const status = allEtudesData[key].status || 'UNKNOWN';
            return {
                name: key,
                status: status,
                is_ok: status === 'OK' || status === 'PARTIAL_SUCCESS',
                is_fail: status === 'FAILED',
                is_warn: status === 'NO_OP',
                actions_log: allEtudesData[key].actions_log
            };
        }).sort((a, b) => { // Sort the array for consistent rendering
            if (a.name === 'zero') return -1;
            if (b.name === 'zero') return 1;
            return a.name.localeCompare(b.name);
        }),
        widget_classes: skin.getClasses(), // Add skin classes to the view data
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
    updateStatusFooter('Initializing...', 'loading');

    // 1. Set up Skin Manager
    const skinManager = new SkinManager();
    [shadeDay, shadeNight, sunMorning, sunAfternoon, sunEvening, sunNight, defaultSkin].forEach(s => skinManager.registerSkin(s));

    // 2. Determine Context and Apply Skin
    const contextFactory = new SkinContextFactory();
    const context = contextFactory.buildContext(['etude:zero']);
    const bestSkin = skinManager.findBestSkin(context);
    skinManager.applySkinCss(bestSkin);

    updateStatusFooter('Fetching latest daily data and template...', 'loading');

    try {
        // 3. Fetch template and data in parallel
        const [template, result] = await Promise.all([
            getTemplate(),
            getLatestEtudeData(REPO_OWNER, REPO_NAME)
        ]);

        // 4. Render content
        if (result.status === 'success') {
            updateStatusFooter(`Skin: ${bestSkin.name} | Data: ${result.version_tag}`, 'success');
            renderAllEtudesStatus(template, result.data, bestSkin);
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
