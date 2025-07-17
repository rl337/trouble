export class Logger {
    constructor(panelId) {
        this.panel = document.getElementById(panelId);
        if (this.panel) {
            this.panel.innerHTML = ''; // Clear the placeholder
        }
    }

    log(message, level = 'INFO') {
        if (!this.panel) return;

        const timestamp = new Date().toISOString();
        const logEntry = document.createElement('div');
        logEntry.style.fontFamily = 'monospace';
        logEntry.style.whiteSpace = 'pre-wrap';
        logEntry.style.borderBottom = '1px solid #eee';
        logEntry.style.padding = '2px 0';

        let color = 'black';
        if (level === 'ERROR') {
            color = 'red';
        } else if (level === 'WARN') {
            color = 'orange';
        }

        logEntry.style.color = color;
        logEntry.textContent = `[${timestamp}] [${level}] ${message}`;

        this.panel.appendChild(logEntry);
        this.panel.scrollTop = this.panel.scrollHeight; // Auto-scroll to bottom
    }

    error(message) {
        this.log(message, 'ERROR');
    }

    warn(message) {
        this.log(message, 'WARN');
    }
}
