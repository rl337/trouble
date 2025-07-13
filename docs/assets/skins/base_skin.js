/**
 * @fileoverview A base class for skin definitions to ensure a common structure.
 */

export class BaseSkin {
    constructor({ name, tags = [], css_file = '', widget_classes = {} }) {
        if (!name) {
            throw new Error("A skin must have a name.");
        }
        this.name = name;
        this.tags = tags;
        this.css_file = css_file;
        this.widget_classes = widget_classes;
    }

    /**
     * Returns the CSS class mappings for common widget types.
     * Subclasses can override this to provide their specific mappings.
     * @returns {object} A dictionary mapping widget type to CSS class name(s).
     */
    getClasses() {
        // Default widget classes can be defined here
        const defaults = {
            title: 'widget-title',
            body: 'widget-body',
            citation: 'widget-citation',
            code_block: 'widget-code-block',
            status_table: 'widget-status-table',
            status_ok: 'status-ok',
            status_fail: 'status-fail',
            status_warn: 'status-warn',
        };

        // Merge defaults with instance-specific classes
        return { ...defaults, ...this.widget_classes };
    }
}
