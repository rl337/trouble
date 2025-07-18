/**
 * @fileoverview Core data fetching logic for etudes.
 */

/**
 * Fetches the latest daily etude data from a GitHub repository's releases.
 *
 * @param {string} owner The owner of the repository.
 * @param {string} repo The name of the repository.
 * @returns {Promise<object>} A promise that resolves to an object with the status and data.
 *
 * The returned object has the shape:
 * - { status: 'success', data: object, version_tag: string }
 * - { status: 'not_found' }
 * - { status: 'error', message: string }
 */
export async function getLatestEtudeData(owner, repo) {
    if (window.MOCK_DATA_URL) {
        console.log(`Using mock data from URL: ${window.MOCK_DATA_URL}`);
        try {
            const response = await fetch(window.MOCK_DATA_URL);
            if (!response.ok) {
                throw new Error(`Failed to fetch mock data: ${response.status}`);
            }
            const data = await response.json();
            return {
                status: 'success',
                data: data,
                version_tag: 'mock_data'
            };
        } catch (error) {
            console.error("Error fetching mock data:", error);
            return { status: 'error', message: error.message };
        }
    }

    const url = `https://api.github.com/repos/${owner}/${repo}/releases/latest`;

    try {
        const response = await fetch(url);

        if (response.status === 404) {
            return { status: 'not_found' };
        }

        if (!response.ok) {
            throw new Error(`GitHub API responded with status ${response.status}`);
        }

        const release = await response.json();
        const asset = release.assets.find(a => a.name === 'daily_etude_data.json');

        if (!asset) {
            return { status: 'not_found' };
        }

        const assetResponse = await fetch(asset.browser_download_url);
        if (!assetResponse.ok) {
            throw new Error(`Failed to download asset with status ${assetResponse.status}`);
        }

        const data = await assetResponse.json();

        return {
            status: 'success',
            data: data,
            version_tag: release.tag_name,
        };
    } catch (error) {
        console.error("Error fetching latest etude data:", error);
        return { status: 'error', message: error.message };
    }
}
