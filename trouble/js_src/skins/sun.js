import { BaseSkin } from './base_skin.js';

// The Sun skin has more specific styles based on time of day.
// It uses a different CSS file from the Shade skin.

// --- Sun Morning Skin ---
export const sunMorning = new BaseSkin({
    name: 'sun_morning',
    tags: ['time_of_day:morning'],
    css_file: '/assets/skins/css/sun.css',
    widget_classes: {
        title: 'sun-title-morning',
        body: 'sun-body-morning',
    },
});

// --- Sun Afternoon Skin ---
export const sunAfternoon = new BaseSkin({
    name: 'sun_afternoon',
    tags: ['time_of_day:afternoon'],
    css_file: '/assets/skins/css/sun.css',
    widget_classes: {
        title: 'sun-title-afternoon',
        body: 'sun-body-afternoon',
    },
});

// --- Sun Evening Skin ---
// This skin can fall back to the generic 'shade_night' skin if the context
// is ['day_period:night', 'time_of_day:evening'].
// Or we can define a specific one.
export const sunEvening = new BaseSkin({
    name: 'sun_evening',
    tags: ['time_of_day:evening'],
    css_file: '/assets/skins/css/sun.css',
    widget_classes: {
        title: 'sun-title-evening',
        body: 'sun-body-evening',
    },
});

// --- Sun Night Skin ---
// A more specific version of shade_night
export const sunNight = new BaseSkin({
    name: 'sun_night',
    tags: ['time_of_day:night'],
    css_file: '/assets/skins/css/sun.css',
    widget_classes: {
        title: 'sun-title-night',
        body: 'sun-body-night',
    },
});
