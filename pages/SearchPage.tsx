
import React, { useState, useMemo } from 'react';
import type { Captain } from '../types';

interface SearchPageProps {
    captains: Captain[];
    onSelectCaptain: (captain: Captain) => void;
    onRateNewCaptain: (name: string) => void;
}

const SearchPage: React.FC<SearchPageProps> = ({ captains, onSelectCaptain, onRateNewCaptain }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredCaptains = useMemo(() => {
        if (!searchTerm.trim()) {
            return captains;
        }
        return captains.filter(captain =>
            captain.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [searchTerm, captains]);

    return (
        <div className="p-4 md:p-8 max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold mb-6 text-cyan-400">Search Captain</h2>
            <div className="mb-6">
                <input
                    type="text"
                    placeholder="Type a captain's name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
            </div>
            <div className="bg-gray-800 rounded-lg shadow-lg">
                <ul className="divide-y divide-gray-700">
                    {filteredCaptains.length > 0 ? (
                        filteredCaptains.map(captain => (
                            <li
                                key={captain.id}
                                onClick={() => onSelectCaptain(captain)}
                                className="p-4 flex justify-between items-center cursor-pointer hover:bg-gray-700/50 transition"
                            >
                                <div>
                                    <p className="font-semibold text-lg">{captain.name}</p>
                                    <p className="text-sm text-gray-400">{captain.base} • {captain.fleet}</p>
                                </div>
                                <span className="text-cyan-400 text-sm">View Profile →</span>
                            </li>
                        ))
                    ) : (
                        searchTerm.trim() ? (
                            <li className="p-6 text-center text-gray-400">
                                <p className="mb-4">Captain "{searchTerm}" not found.</p>
                                <button
                                    onClick={() => onRateNewCaptain(searchTerm)}
                                    className="bg-cyan-500 text-white font-bold py-2 px-4 rounded-md hover:bg-cyan-600 transition"
                                >
                                    Be the first to rate them
                                </button>
                            </li>
                        ) : (
                             <li className="p-4 text-center text-gray-500">No captains found.</li>
                        )
                    )}
                </ul>
            </div>
        </div>
    );
};

export default SearchPage;
