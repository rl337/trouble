/**
 * @fileoverview Core library for fetching the latest daily etude data from GitHub Releases.
 */

/**
 * Formats a date object as YYYY-MM-DD.
 * @param {Date} date The date to format.
 * @returns {string} The formatted date string.
 */
function getFormattedDate(date) {
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Fetches the latest daily etude data from GitHub Releases, trying today first,
 * then previous days up to a specified limit.
 *
 * @param {string} repoOwner The owner of the GitHub repository.
 * @param {string} repoName The name of the GitHub repository.
 * @param {string} [baseTagPrefix="data-"] The prefix for the date-based release tags.
 * @param {number} [daysToTry=7] The number of past days to check for a valid release if today's is not found.
 * @returns {Promise<{status: 'success'|'error'|'not_found', data: object|null, version_tag: string|null, message: string}>}
 *          An object containing the fetch status, the data, the tag of the version found, and a log message.
 */
/**
 * A helper function to introduce a delay.
 * @param {number} ms The number of milliseconds to wait.
 * @returns {Promise<void>}
 */
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Fetches the latest daily etude data from GitHub Releases, trying today first,
 * then previous days up to a specified limit, with retries for transient errors.
 *
 * @param {string} repoOwner The owner of the GitHub repository.
 * @param {string} repoName The name of the GitHub repository.
 * @param {string} [baseTagPrefix="data-"] The prefix for the date-based release tags.
 * @param {number} [daysToTry=7] The number of past days to check for a valid release.
 * @param {number} [maxRetries=2] The number of retries for a single URL if a network error occurs.
 * @param {number} [retryDelay=1000] The delay in ms between retries.
 * @returns {Promise<{status: 'success'|'error'|'not_found', data: object|null, version_tag: string|null, message: string}>}
 */
export async function getLatestEtudeData(repoOwner, repoName, {
    baseTagPrefix = "data-",
    daysToTry = 7,
    maxRetries = 2,
    retryDelay = 1000
} = {}) {
    if (!repoOwner || !repoName) {
        return { status: 'error', data: null, version_tag: null, message: "Repository owner and name must be provided." };
    }

    const ASSET_NAME = "daily_etude_data.json";

    for (let dayIndex = 0; dayIndex < daysToTry; dayIndex++) {
        const date = new Date();
        date.setUTCDate(date.getUTCDate() - dayIndex);
        const dateString = getFormattedDate(date);
        const tagName = `${baseTagPrefix}${dateString}`;
        const assetUrl = `https://github.com/${repoOwner}/${repoName}/releases/download/${tagName}/${ASSET_NAME}`;

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            console.log(`Attempt ${attempt + 1}/${maxRetries + 1} for tag: ${tagName} from ${assetUrl}`);

            try {
                const dataResponse = await fetch(assetUrl);

                if (dataResponse.ok) {
                    const etudeData = await dataResponse.json();
                    console.log(`Successfully fetched and parsed data for ${tagName}.`);
                    return {
                        status: 'success',
                        data: etudeData,
                        version_tag: tagName,
                        message: `Successfully loaded data from release ${tagName}.`
                    };
                }

                if (dataResponse.status === 404) {
                    console.log(`Asset for tag ${tagName} not found. Trying previous day.`);
                    break; // Break the retry loop for this day and move to the previous day
                }

                // For other non-OK statuses (5xx, etc.), we treat it as a potentially transient error and retry.
                console.warn(`Fetch failed with status ${dataResponse.status}. Retrying after ${retryDelay}ms...`);
                if (attempt < maxRetries) await delay(retryDelay);

            } catch (error) {
                // This catches network errors (e.g., DNS, connection refused)
                console.error(`Network error for tag ${tagName}:`, error);
                if (attempt < maxRetries) {
                    console.warn(`Retrying after ${retryDelay}ms...`);
                    await delay(retryDelay);
                }
            }
        }
    }

    // If the loop completes without returning, no data was found
    return {
        status: 'not_found',
        data: null,
        version_tag: null,
        message: `Could not find a valid data release after checking the last ${daysToTry} days.`
    };
}

// Example of how this might be used in an etude's JS file:
/*
import { getLatestEtudeData } from './core/data_fetcher.js';

document.addEventListener('DOMContentLoaded', async () => {
    const repoOwner = 'your-github-username'; // This needs to be configured
    const repoName = 'your-repo-name';       // This needs to be configured

    const result = await getLatestEtudeData(repoOwner, repoName);

    if (result.status === 'success') {
        console.log('Loaded data version:', result.version_tag);
        // Now render the page using result.data
        // e.g., renderEtudeOne(result.data.one);
    } else {
        console.error('Failed to load daily data:', result.message);
        // Update UI to show an error message
    }
});
*/
