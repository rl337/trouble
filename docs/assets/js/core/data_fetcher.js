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
export async function getLatestEtudeData(repoOwner, repoName, baseTagPrefix = "data-", daysToTry = 7) {
    if (!repoOwner || !repoName) {
        return {
            status: 'error',
            data: null,
            version_tag: null,
            message: "Repository owner and name must be provided."
        };
    }

    const GITHUB_API_BASE = "https://api.github.com";
    const ASSET_NAME = "daily_etude_data.json";

    for (let i = 0; i < daysToTry; i++) {
        const date = new Date();
        date.setUTCDate(date.getUTCDate() - i);
        const dateString = getFormattedDate(date);
        const tagName = `${baseTagPrefix}${dateString}`;

        const releaseUrl = `${GITHUB_API_BASE}/repos/${repoOwner}/${repoName}/releases/tags/${tagName}`;

        console.log(`Attempting to fetch release metadata for tag: ${tagName} from ${releaseUrl}`);

        try {
            const releaseResponse = await fetch(releaseUrl);

            if (!releaseResponse.ok) {
                if (releaseResponse.status === 404) {
                    console.log(`Release with tag ${tagName} not found. Trying previous day.`);
                    continue; // Go to the next iteration (previous day)
                }
                throw new Error(`GitHub API returned status ${releaseResponse.status} for release metadata.`);
            }

            const releaseData = await releaseResponse.json();
            const asset = releaseData.assets?.find(a => a.name === ASSET_NAME);

            if (!asset) {
                console.log(`Release ${tagName} found, but asset '${ASSET_NAME}' is missing. Trying previous day.`);
                continue; // Asset not found, try previous day
            }

            console.log(`Found asset '${ASSET_NAME}' for tag ${tagName}. Fetching data from: ${asset.browser_download_url}`);

            // The browser_download_url is a direct link, but may be subject to CORS issues if the API
            // that serves it doesn't have the right headers. GitHub release assets are generally fine.
            // Using a fetch request with no-cors might be needed if issues arise, but can limit what you do with the response.
            // For public repos, this should generally work.
            const dataResponse = await fetch(asset.browser_download_url);

            if (!dataResponse.ok) {
                throw new Error(`Failed to download asset '${ASSET_NAME}' with status ${dataResponse.status}`);
            }

            const etudeData = await dataResponse.json();

            console.log(`Successfully fetched and parsed data for ${tagName}.`);
            return {
                status: 'success',
                data: etudeData,
                version_tag: tagName,
                message: `Successfully loaded data from release ${tagName}.`
            };

        } catch (error) {
            console.error(`Error fetching data for tag ${tagName}:`, error);
            // If there's a network error or other issue, we might want to stop trying.
            // For now, we'll log it and continue to the next day as it might be a transient issue.
            // If after all days we still fail, the final return will indicate the error.
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
