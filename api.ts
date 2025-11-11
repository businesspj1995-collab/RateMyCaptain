import type { Captain, Rating } from './types';
import { initialCaptains, initialRatings } from './mockData';

// --- LocalStorage Implementation ---
// This is the current implementation. It uses the browser's localStorage,
// which is device-specific. To enable cross-device data syncing, you would
// replace the functions below with calls to your backend API.

const CAPTAINS_KEY = 'captains';
const RATINGS_KEY = 'ratings';

export const loadData = async (): Promise<{ captains: Captain[], ratings: Rating[] }> => {
    console.log("Attempting to load data...");
    try {
        const savedCaptains = localStorage.getItem(CAPTAINS_KEY);
        const savedRatings = localStorage.getItem(RATINGS_KEY);

        if (savedCaptains && savedRatings) {
            console.log("Found data in localStorage.");
            return {
                captains: JSON.parse(savedCaptains),
                ratings: JSON.parse(savedRatings),
            };
        } else {
            // Seed with initial data if localStorage is empty
            console.log("No data in localStorage, seeding with initial data.");
            await saveData(initialCaptains, initialRatings);
            return { captains: initialCaptains, ratings: initialRatings };
        }
    } catch (error) {
        console.error("Error loading from localStorage, using initial data", error);
        return { captains: initialCaptains, ratings: initialRatings };
    }
};

export const saveData = async (captains: Captain[], ratings: Rating[]): Promise<void> => {
     try {
        console.log("Saving data to localStorage...");
        localStorage.setItem(CAPTAINS_KEY, JSON.stringify(captains));
        localStorage.setItem(RATINGS_KEY, JSON.stringify(ratings));
    } catch (error) {
        console.error("Failed to save to localStorage", error);
    }
};

// --- Backend API Implementation (Example) ---
/*
To make this app work across devices, you would host a backend server with a database.
Then, you would replace the LocalStorage functions above with something like this:

const API_BASE_URL = 'https://your-backend-api.com';

export const loadData = async (): Promise<{ captains: Captain[], ratings: Rating[] }> => {
    try {
        const [captainsResponse, ratingsResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/captains`),
            fetch(`${API_BASE_URL}/ratings`)
        ]);

        if (!captainsResponse.ok || !ratingsResponse.ok) {
            throw new Error('Failed to fetch data from the server.');
        }

        const captains = await captainsResponse.json();
        const ratings = await ratingsResponse.json();
        
        return { captains, ratings };
    } catch (error) {
        console.error("Failed to load data from API", error);
        // Fallback or error handling
        return { captains: [], ratings: [] };
    }
};

// This is a simplified example. In a real app, you would likely have more 
// granular endpoints, e.g., POST /ratings for a new rating, etc.
export const saveData = async (captains: Captain[], ratings: Rating[]): Promise<void> => {
    try {
        await fetch(`${API_BASE_URL}/data/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ captains, ratings })
        });
    } catch (error) {
        console.error("Failed to save data to API", error);
    }
};
*/
