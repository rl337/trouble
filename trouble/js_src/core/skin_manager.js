/**
 * @fileoverview Manages skin discovery, context generation, and application.
 */

// --- SkinContextFactory ---

/**
 * A Tagger function generates context tags based on environment or other factors.
 * @callback Tagger
 * @returns {string[]} An array of context tags, e.g., ["season:summer", "time_of_day:morning"].
 */

/**
 * Creates a context for skin selection by running various "Taggers".
 */
export class SkinContextFactory {
    constructor() {
        /** @type {Tagger[]} */
        this.taggers = [];
        this.registerDefaultTaggers();
    }

    /**
     * Registers the default environment-aware taggers.
     */
    registerDefaultTaggers() {
        this.registerTagger(this.timeOfDayTagger);
        this.registerTagger(this.seasonOfYearTagger);
    }

    /**
     * Adds a new tagger function to the factory.
     * @param {Tagger} tagger
     */
    registerTagger(tagger) {
        if (typeof tagger === 'function') {
            this.taggers.push(tagger);
        }
    }

    /**
     * Builds the final context array by running all registered taggers
     * and combining the results with any provided additional tags.
     * @param {string[]} [additionalTags=[]] - Tags specific to the call site (e.g., ['etude:one']).
     * @returns {string[]} The complete context tag array.
     */
    buildContext(additionalTags = []) {
        let context = [...additionalTags];
        for (const tagger of this.taggers) {
            context.push(...tagger());
        }
        // Return a unique set of tags
        return [...new Set(context)];
    }

    // --- Default Tagger Implementations ---

    timeOfDayTagger() {
        const hour = new Date().getHours();
        const tags = [];
        if (hour >= 5 && hour < 12) {
            tags.push("time_of_day:morning");
            tags.push("day_period:day");
        } else if (hour >= 12 && hour < 18) {
            tags.push("time_of_day:afternoon");
            tags.push("day_period:day");
        } else if (hour >= 18 && hour < 22) {
            tags.push("time_of_day:evening");
            tags.push("day_period:night");
        } else {
            tags.push("time_of_day:night");
            tags.push("day_period:night");
        }
        return tags;
    }

    seasonOfYearTagger() {
        // Simple Northern Hemisphere calculation
        const month = new Date().getMonth(); // 0-11
        if (month >= 2 && month <= 4) return ["season:spring"]; // Mar, Apr, May
        if (month >= 5 && month <= 7) return ["season:summer"]; // Jun, Jul, Aug
        if (month >= 8 && month <= 10) return ["season:fall"];   // Sep, Oct, Nov
        return ["season:winter"]; // Dec, Jan, Feb
    }
}


// --- SkinManager ---

/**
 * Discovers, registers, and applies skins based on context.
 */
export class SkinManager {
    constructor() {
        /** @type {object[]} */
        this.registeredSkins = [];
    }

    /**
     * Registers a skin definition object.
     * @param {object} skinObject
     */
    registerSkin(skinObject) {
        if (skinObject && skinObject.name) {
            this.registeredSkins.push(skinObject);
        }
    }

    /**
     * Finds the best skin that matches the current context.
     * The "best" skin is the one with the most matching tags, provided its
     * tags are a strict subset of the context tags.
     * @param {string[]} contextArray - The current context tags.
     * @returns {object|null} The best matching skin object or null if none found.
     */
    findBestSkin(contextArray) {
        let bestSkins = [];
        let maxScore = -1;

        const contextSet = new Set(contextArray);

        for (const skin of this.registeredSkins) {
            const skinTags = new Set(skin.tags || []);

            // Check if the skin's tags are a subset of the context's tags.
            const isSubset = [...skinTags].every(tag => contextSet.has(tag));

            if (isSubset) {
                const score = skinTags.size;
                if (score > maxScore) {
                    maxScore = score;
                    bestSkins = [skin];
                } else if (score === maxScore) {
                    bestSkins.push(skin);
                }
            }
        }

        if (bestSkins.length === 0) {
            // If no match, find the default skin (no tags)
            const defaultSkin = this.registeredSkins.find(s => s.tags.length === 0);
            console.log(`No specific skin found. Falling back to default:`, defaultSkin?.name || 'none');
            return defaultSkin || null;
        }

        if (bestSkins.length > 1) {
            // In case of a tie in score, sort by name to ensure determinism
            console.warn(`Multiple skins found with the same score (${maxScore}). Sorting by name to break the tie.`, bestSkins.map(s => s.name));
            bestSkins.sort((a, b) => a.name.localeCompare(b.name));
        }

        const chosenSkin = bestSkins[0];
        console.log(`Best skin found for context [${contextArray.join(', ')}]:`, chosenSkin?.name || 'none');
        return chosenSkin;
    }

    /**
     * Dynamically loads a skin's CSS file into the document's head.
     * @param {object} skinObject
     */
    applySkinCss(skinObject) {
        if (!skinObject || !skinObject.css_file) return;

        // Check if this stylesheet is already loaded
        const linkId = `skin-css-${skinObject.name}`;
        if (document.getElementById(linkId)) {
            return; // Already loaded
        }

        const link = document.createElement('link');
        link.id = linkId;
        link.rel = 'stylesheet';
        link.href = skinObject.css_file;
        document.head.appendChild(link);
        console.log(`Applied CSS: ${skinObject.css_file}`);
    }
}
