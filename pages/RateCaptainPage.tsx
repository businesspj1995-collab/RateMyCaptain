import React, { useState } from 'react';
import type { Captain, Rating, Base, Fleet } from '../types';
import { BASES, FLEETS, RATING_GROUPS, SOCIAL_INTERACTION_SCALE_GUIDE, MENTORSHIP_SCALE_GUIDE } from '../constants';
import RatingSlider from '../components/RatingSlider';
import ToggleSwitch from '../components/ToggleSwitch';

interface RateCaptainPageProps {
    captains: Captain[];
    onAddRating: (rating: Omit<Rating, 'id'>, captainInfo: Omit<Captain, 'id'>) => void;
    onFinish: () => void;
    initialName?: string;
}

const RateCaptainPage: React.FC<RateCaptainPageProps> = ({ captains, onAddRating, onFinish, initialName }) => {
    const [name, setName] = useState(initialName || '');
    const [base, setBase] = useState<Base>(BASES[0]);
    const [fleet, setFleet] = useState<Fleet>(FLEETS[0]);

    const [ratings, setRatings] = useState({
        professionalism: 3,
        crm: 3,
        communication: 3,
        easeToFlyWith: 3,
        micromanagement: 3,
        cabinCrewInteraction: 3,
        wouldFlyAgain: 3,
        helpsWithBoxWork: true,
        helpsWithWalkarounds: true,
        mentorship: 3,
        socialInteraction: 3,
        metAtJet: true,
    });

    const handleRatingChange = <T extends keyof typeof ratings>(key: T, value: (typeof ratings)[T]) => {
        setRatings(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) {
            alert("Captain's name is required.");
            return;
        }

        const existingCaptain = captains.find(c => c.name.toLowerCase() === name.trim().toLowerCase());
        const captainId = existingCaptain ? existingCaptain.id : `new_${Date.now()}`;
        
        const newRating: Omit<Rating, 'id'> = {
            captainId,
            ...ratings
        };
        
        const captainInfo: Omit<Captain, 'id'> = {
            name: name.trim(),
            base,
            fleet,
        };

        onAddRating(newRating, captainInfo);
        onFinish();
    };
    
    return (
        <div className="p-4 md:p-8 max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold mb-6 text-cyan-400">Rate a Captain</h2>
            <form onSubmit={handleSubmit} className="space-y-8">
                <div className="p-6 bg-gray-800 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4">Captain Info</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                            <input
                                type="text"
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                list="captains-list"
                                required
                                className="w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white"
                            />
                            <datalist id="captains-list">
                                {captains.map(c => <option key={c.id} value={c.name} />)}
                            </datalist>
                        </div>
                        <div>
                            <label htmlFor="base" className="block text-sm font-medium text-gray-300 mb-1">Base</label>
                            <select id="base" value={base} onChange={(e) => setBase(e.target.value as Base)} className="w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white">
                                {BASES.map(b => <option key={b} value={b}>{b}</option>)}
                            </select>
                        </div>
                        <div>
                            <label htmlFor="fleet" className="block text-sm font-medium text-gray-300 mb-1">Fleet</label>
                            <select id="fleet" value={fleet} onChange={(e) => setFleet(e.target.value as Fleet)} className="w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white">
                                {FLEETS.map(f => <option key={f} value={f}>{f}</option>)}
                            </select>
                        </div>
                    </div>
                </div>

                <div className="p-6 bg-gray-800 rounded-lg">
                    <h3 className="text-xl font-semibold mb-2">Core Metrics</h3>
                     <div className="divide-y divide-gray-700">
                        {Object.entries(RATING_GROUPS.SCORED_SCALE).map(([key, config]) => {
                            const ratingKey = key as keyof typeof ratings;
                            return (
                                <RatingSlider 
                                    key={key}
                                    label={config.label}
                                    description={config.description}
                                    value={ratings[ratingKey] as number}
                                    onChange={(v) => handleRatingChange(ratingKey, v)}
                                />
                            );
                        })}
                        {Object.entries(RATING_GROUPS.SCORED_TOGGLE).map(([key, config]) => {
                            const ratingKey = key as keyof typeof ratings;
                            return (
                                <ToggleSwitch
                                    key={key}
                                    label={config.label}
                                    description={config.description}
                                    value={ratings[ratingKey] as boolean}
                                    onChange={(v) => handleRatingChange(ratingKey, v)}
                                />
                            );
                        })}
                    </div>
                </div>

                <div className="p-6 bg-gray-800 rounded-lg">
                    <h3 className="text-xl font-semibold mb-2">Personal Preferences</h3>
                    <p className="text-sm text-gray-400 mb-4">
                        These items are subjective and do not affect the captain's overall score. They are shown on profiles for informational purposes only.
                    </p>
                    <div className="divide-y divide-gray-700">
                        {Object.entries(RATING_GROUPS.PREFERENCES).map(([key, config]) => {
                            const ratingKey = key as keyof typeof ratings;
                            if (config.type === 'scale') {
                                return (
                                    <RatingSlider 
                                        key={key}
                                        label={config.label}
                                        description={config.description}
                                        value={ratings[ratingKey] as number}
                                        onChange={(v) => handleRatingChange(ratingKey, v)}
                                        scaleGuide={
                                            key === 'socialInteraction' ? SOCIAL_INTERACTION_SCALE_GUIDE :
                                            key === 'mentorship' ? MENTORSHIP_SCALE_GUIDE :
                                            undefined
                                        }
                                    />
                                );
                            } else {
                                return (
                                    <ToggleSwitch
                                        key={key}
                                        label={config.label}
                                        description={config.description}
                                        value={ratings[ratingKey] as boolean}
                                        onChange={(v) => handleRatingChange(ratingKey, v)}
                                    />
                                );
                            }
                        })}
                    </div>
                </div>

                <button type="submit" className="w-full bg-cyan-500 text-white font-bold py-3 px-6 rounded-md hover:bg-cyan-600 transition text-lg">
                    Submit Anonymous Rating
                </button>
            </form>
        </div>
    );
};

export default RateCaptainPage;