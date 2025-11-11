import type { Captain, Rating } from './types';
import { Base, Fleet } from './types';

// MOCK DATA for first-time users
export const initialCaptains: Captain[] = [
    { id: '1', name: 'J. Smith', base: Base.ORD, fleet: Fleet.B737 },
    { id: '2', name: 'A. Williams', base: Base.IAH, fleet: Fleet.B777 },
    { id: '3', name: 'M. Brown', base: Base.DEN, fleet: Fleet.A320 },
    { id: '4', name: 'K. Jones', base: Base.SFO, fleet: Fleet.B787 },
    { id: '5', name: 'D. Miller', base: Base.LAX, fleet: Fleet.B757 },
];

const generateRandomRating = (captainId: string): Omit<Rating, 'id'> => ({
    captainId,
    professionalism: Math.floor(Math.random() * 2) + 4, // 4-5
    crm: Math.floor(Math.random() * 2) + 4, // 4-5
    communication: Math.floor(Math.random() * 2) + 4, // 4-5
    easeToFlyWith: Math.floor(Math.random() * 3) + 3, // 3-5
    micromanagement: Math.floor(Math.random() * 2) + 4, // 4-5
    cabinCrewInteraction: Math.floor(Math.random() * 2) + 4, // 4-5
    wouldFlyAgain: Math.floor(Math.random() * 2) + 4, // 4-5
    helpsWithBoxWork: Math.random() > 0.1,
    helpsWithWalkarounds: Math.random() > 0.2,
    mentorship: Math.floor(Math.random() * 3) + 3, // 3-5
    socialInteraction: Math.floor(Math.random() * 5) + 1, // 1-5
    metAtJet: Math.random() > 0.05,
});

export const initialRatings: Rating[] = initialCaptains.flatMap(captain => 
    Array.from({ length: Math.floor(Math.random() * 15) + 5 }, (_, i) => ({
        id: `${captain.id}-${i}`,
        ...generateRandomRating(captain.id),
    }))
);
