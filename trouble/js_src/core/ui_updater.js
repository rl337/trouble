/**
 * @fileoverview Core UI helper functions for updating the DOM.
 */

/**
 * Sets the text content of an element by its ID.
 * @param {string} elementId The ID of the DOM element.
 * @param {string} text The text to set.
 */
export function setText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    } else {
        console.warn(`UI Updater: Element with id '${elementId}' not found.`);
    }
}

/**
 * Sets the inner HTML of an element by its ID. Use with trusted HTML.
 * @param {string} elementId The ID of the DOM element.
 * @param {string} html The HTML string to set.
 */
export function setHtml(elementId, html) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = html;
    } else {
        console.warn(`UI Updater: Element with id '${elementId}' not found.`);
    }
}

/**
 * Shows an element by setting its display style to 'block' (or a custom value).
 * @param {string} elementId The ID of the DOM element.
 * @param {string} [displayValue='block'] The display style to apply.
 */
export function showElement(elementId, displayValue = 'block') {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = displayValue;
    } else {
        console.warn(`UI Updater: Element with id '${elementId}' not found.`);
    }
}

/**
 * Hides an element by setting its display style to 'none'.
 * @param {string} elementId The ID of the DOM element.
 */
export function hideElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    } else {
        console.warn(`UI Updater: Element with id '${elementId}' not found.`);
    }
}

/**
 * Updates the status footer with a message.
 * @param {string} message The message to display.
 * @param {'success'|'error'|'loading'|'warning'} [status='loading'] The status type, for styling.
 */
export function updateStatusFooter(message, status = 'loading') {
    const footerId = 'etude_status_footer'; // A conventional ID for the footer
    const footer = document.getElementById(footerId);
    if (footer) {
        footer.textContent = message;
        // Reset classes
        footer.classList.remove('status-success', 'status-error', 'status-loading', 'status-warning');
        // Add new status class for styling
        if (status === 'success') {
            footer.classList.add('status-success');
        } else if (status === 'error') {
            footer.classList.add('status-error');
        } else if (status === 'warning') {
            footer.classList.add('status-warning');
        } else { // 'loading' or default
            footer.classList.add('status-loading');
        }
    } else {
        console.warn(`UI Updater: Status footer with id '${footerId}' not found.`);
    }
}
