import { BaseSkin } from './base_skin.js';

// The default skin has no tags, so it acts as a fallback.
// It provides a very basic, unstyled look.
export const defaultSkin = new BaseSkin({
    name: 'default',
    tags: [],
    css_file: '/assets/skins/css/default.css',
    // It can rely on the default widget classes from BaseSkin,
    // or define its own if needed.
    widget_classes: {
        title: 'default-title',
        body: 'default-body',
    },
});
