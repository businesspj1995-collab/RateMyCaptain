import { Base, Fleet } from './types';

export const ACCESS_CODE = "FOmatters";

export const BASES = Object.values(Base);
export const FLEETS = Object.values(Fleet);

const SCORED_SCALE_CATEGORIES = {
    professionalism: { label: 'Professionalism', description: 'Calm, respectful, level-headed.', scored: true, type: 'scale' as const },
    crm: { label: 'CRM (Crew Resource Management)', description: 'Involves the FO, communicates, and works as a team.', scored: true, type: 'scale' as const },
    communication: { label: 'Communication (Flight-Related)', description: 'Clear and concise with ATC, procedures, and coordination.', scored: true, type: 'scale' as const },
    easeToFlyWith: { label: 'Ease to Fly With', description: 'Relaxed, adaptable, easy cockpit vibe.', scored: true, type: 'scale' as const },
    micromanagement: { label: 'Micromanagement Level', description: '1 = Over-controlling, 5 = Trusts you to fly.', scored: true, type: 'scale' as const },
    cabinCrewInteraction: { label: 'Cabin Crew Interaction', description: 'Professional and respectful toward flight attendants.', scored: true, type: 'scale' as const },
    wouldFlyAgain: { label: 'Would You Fly With Them Again?', description: '1 = No, 5 = Absolutely.', scored: true, type: 'scale' as const },
};

const SCORED_TOGGLE_CATEGORIES = {
    helpsWithBoxWork: { label: 'Helps with Box Work', description: 'Assists with FMS setup, routing, or performance entries.', scored: true, type: 'toggle' as const },
    helpsWithWalkarounds: { label: 'Helps with Walkarounds', description: 'Offers or trades off exterior walkarounds.', scored: true, type: 'toggle' as const },
};

const PREFERENCE_CATEGORIES = {
    mentorship: { label: 'Mentorship / Coaching', description: 'Shares knowledge or experience when appropriate.', scored: false, type: 'scale' as const },
    socialInteraction: { label: 'Social Interaction (Non-Flight)', description: '1 = Strictly flight-related, 5 = Very talkative.', scored: false, type: 'scale' as const },
    metAtJet: { label: 'Met at the Jet', description: 'Did they meet you at the jet before departure?', scored: false, type: 'toggle' as const },
};

export const RATING_GROUPS = {
    SCORED_SCALE: SCORED_SCALE_CATEGORIES,
    SCORED_TOGGLE: SCORED_TOGGLE_CATEGORIES,
    PREFERENCES: PREFERENCE_CATEGORIES,
};

export const RATING_CATEGORIES = {
    ...SCORED_SCALE_CATEGORIES,
    ...SCORED_TOGGLE_CATEGORIES,
    ...PREFERENCE_CATEGORIES,
};

export const SCALE_GUIDE: { [key: number]: string } = {
    1: 'Not great',
    2: 'Needs improvement',
    3: 'Average',
    4: 'Good',
    5: 'Excellent',
};

export const SOCIAL_INTERACTION_SCALE_GUIDE: { [key: number]: string } = {
    1: 'Strictly flight-related',
    2: 'Mostly flight-related',
    3: 'Moderate social chat',
    4: 'Quite talkative',
    5: "Very talkative",
};

export const MENTORSHIP_SCALE_GUIDE: { [key: number]: string } = {
    1: 'No mentorship offered',
    2: 'Minimal coaching',
    3: 'Offers advice when asked',
    4: 'Proactive with helpful tips',
    5: 'Excellent, willing mentor',
};
