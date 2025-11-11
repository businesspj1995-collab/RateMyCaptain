import React, { useState, useMemo } from 'react';
import type { Captain, Rating } from '../types';

interface HomePageProps {
    captains: Captain[];
    ratings: Rating[];
    onSelectCaptain: (captain: Captain) => void;
    onRateNewCaptain: (name: string) => void;
}

const HomePage: React.FC<HomePageProps> = ({ captains, ratings, onSelectCaptain, onRateNewCaptain }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const recentlyRatedCaptains = [...ratings]
        .slice(-5)
        .reverse()
        .map(r => captains.find(c => c.id === r.captainId))
        .filter((c, index, self) => c && self.findIndex(cap => cap.id === c.id) === index)
        .slice(0, 3);
    
    const suggestedCaptains = useMemo(() => {
        if (searchTerm.trim().length < 2) {
            return [];
        }
        return captains
            .filter(captain =>
                captain.name.toLowerCase().includes(searchTerm.toLowerCase())
            )
            .slice(0, 5); // Limit suggestions
    }, [searchTerm, captains]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const term = searchTerm.trim();
        if (!term) return;

        const exactMatch = captains.find(c => c.name.toLowerCase() === term.toLowerCase());
        
        if (exactMatch) {
            onSelectCaptain(exactMatch);
        } else {
            onRateNewCaptain(term);
        }
    };

    const handleSuggestionClick = (captain: Captain) => {
        setSearchTerm(captain.name);
        onSelectCaptain(captain);
    };
    
    return (
        <div className="p-4 md:p-8">
            <div className="text-center bg-gray-800 p-8 rounded-lg shadow-lg">
                <h2 className="text-4xl font-bold text-white">Built by FOs, for FOs.</h2>
                <p className="text-gray-300 mt-2 max-w-2xl mx-auto">A simple, anonymous way for First Officers to rate Captains based on real flight-deck experiences.</p>
                <div className="mt-8 max-w-xl mx-auto relative">
                    <form onSubmit={handleSearchSubmit}>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Find or rate a captain..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full p-4 pr-20 bg-gray-700 border border-gray-600 rounded-md text-white text-lg placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                            />
                            <button
                                type="submit"
                                className="absolute right-2 top-1/2 -translate-y-1/2 bg-cyan-500 text-white font-bold py-2 px-4 rounded-md hover:bg-cyan-600 transition"
                            >
                                Go
                            </button>
                        </div>
                    </form>
                    {suggestedCaptains.length > 0 && searchTerm.trim().length > 0 && (
                        <ul className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-md shadow-lg text-left">
                            {suggestedCaptains.map(captain => (
                                <li
                                    key={captain.id}
                                    onClick={() => handleSuggestionClick(captain)}
                                    className="px-4 py-3 cursor-pointer hover:bg-gray-600 transition-colors"
                                >
                                    {captain.name}
                                </li>
                            ))}
                            <li 
                                className="px-4 py-3 cursor-pointer text-cyan-400 hover:bg-gray-600 transition-colors"
                                onClick={() => onRateNewCaptain(searchTerm.trim())}
                            >
                                Can't find them? Rate "{searchTerm.trim()}" as a new captain.
                            </li>
                        </ul>
                    )}
                </div>
            </div>

            <div className="mt-12">
                <h3 className="text-2xl font-semibold mb-4 text-center text-cyan-400">Recently Rated Captains</h3>
                {ratings.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {recentlyRatedCaptains.map(captain => captain && (
                            <div key={captain.id} onClick={() => onSelectCaptain(captain)} className="bg-gray-800 p-6 rounded-lg shadow-md text-center cursor-pointer hover:bg-gray-700/50 transition">
                                <p className="text-xl font-bold">{captain.name}</p>
                                <p className="text-gray-400">{captain.base} • {captain.fleet}</p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-center text-gray-500">No ratings submitted yet.</p>
                )}
            </div>

             <div className="mt-12 p-6 bg-gray-800 rounded-lg">
                <h3 className="text-2xl font-semibold mb-4 text-cyan-400">Guidelines</h3>
                <ul className="list-disc list-inside space-y-2 text-gray-300">
                    <li>Made by pilots — not management.</li>
                    <li>All feedback stays anonymous.</li>
                    <li>Keep it fair, factual, and based on actual flights.</li>
                    <li>A higher score = a better experience in the cockpit.</li>
                </ul>
            </div>
        </div>
    );
};

export default HomePage;