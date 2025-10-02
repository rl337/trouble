import { BaseSkin } from './base_skin.js';

// --- Shade Day Skin ---
const shadeDayClasses = {
    title: 'shade-title-day',
    body: 'shade-body-day',
    // other widget classes can be defined here
};

export const shadeDay = new BaseSkin({
    name: 'shade_day',
    tags: ['day_period:day'],
    css_file: '../assets/skins/css/shade.css',
    widget_classes: shadeDayClasses,
});


// --- Shade Night Skin ---
const shadeNightClasses = {
    title: 'shade-title-night',
    body: 'shade-body-night',
    // other widget classes can be defined here
};

export const shadeNight = new BaseSkin({
    name: 'shade_night',
    tags: ['day_period:night'],
    css_file: '../assets/skins/css/shade.css',
    widget_classes: shadeNightClasses,
});
