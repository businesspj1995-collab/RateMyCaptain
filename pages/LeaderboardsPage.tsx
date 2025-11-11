
import React, { useState, useMemo, useCallback } from 'react';
import type { Captain, Rating, Base, Fleet } from '../types';
import { RATING_CATEGORIES, BASES, FLEETS } from '../constants';

interface LeaderboardsPageProps {
    captains: Captain[];
    ratings: Rating[];
    onSelectCaptain: (captain: Captain) => void;
}

const LeaderboardsPage: React.FC<LeaderboardsPageProps> = ({ captains, ratings, onSelectCaptain }) => {
    const [filterBase, setFilterBase] = useState<Base>(BASES[0]);
    const [filterFleet, setFilterFleet] = useState<Fleet>(FLEETS[0]);

    const calculateOverallScore = useCallback((captainId: string): number | null => {
        const captainRatings = ratings.filter(r => r.captainId === captainId);
        if (captainRatings.length === 0) return null;

        let totalScore = 0;
        let scoredItemsCount = 0;

        Object.entries(RATING_CATEGORIES).forEach(([key, config]) => {
            if (config.scored) {
                const ratingKey = key as keyof Rating;
                const avg = captainRatings.reduce((acc, r) => {
                    const val = r[ratingKey];
                    if (typeof val === 'number') return acc + val;
                    if (typeof val === 'boolean') return acc + (val ? 5 : 1); // Yes = 5, No = 1 for score
                    return acc;
                }, 0) / captainRatings.length;
                totalScore += avg;
                scoredItemsCount++;
            }
        });

        return totalScore / scoredItemsCount;
    }, [ratings]);

    const topByBase = useMemo(() => {
        return captains
            .filter(c => c.base === filterBase)
            .map(c => ({ ...c, score: calculateOverallScore(c.id) }))
            .filter(c => c.score !== null)
            .sort((a, b) => (b.score as number) - (a.score as number))
            .slice(0, 5);
    }, [captains, filterBase, calculateOverallScore]);

    const topByFleet = useMemo(() => {
        return captains
            .filter(c => c.fleet === filterFleet)
            .map(c => ({ ...c, score: calculateOverallScore(c.id) }))
            .filter(c => c.score !== null)
            .sort((a, b) => (b.score as number) - (a.score as number))
            .slice(0, 5);
    }, [captains, filterFleet, calculateOverallScore]);

    const LeaderboardList: React.FC<{data: (Captain & {score: number | null})[]}> = ({ data }) => (
         <ul className="divide-y divide-gray-700">
            {data.length > 0 ? data.map((captain, index) => (
                <li key={captain.id} onClick={() => onSelectCaptain(captain)} className="p-3 flex items-center justify-between cursor-pointer hover:bg-gray-700/50">
                    <div className="flex items-center">
                        <span className="text-lg font-bold w-8 text-center text-cyan-400">{index + 1}</span>
                        <div>
                            <p className="font-semibold">{captain.name}</p>
                            <p className="text-sm text-gray-400">{captain.base} • {captain.fleet}</p>
                        </div>
                    </div>
                    <span className="text-lg font-bold text-white">{captain.score?.toFixed(2)}</span>
                </li>
            )) : <li className="p-4 text-center text-gray-500">Not enough data.</li>}
        </ul>
    );

    return (
        <div className="p-4 md:p-8 max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold mb-8 text-center text-cyan-400">Top Captains</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* By Base */}
                <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xl font-semibold">By Base</h3>
                        <select value={filterBase} onChange={e => setFilterBase(e.target.value as Base)} className="bg-gray-700 border border-gray-600 rounded-md p-1 text-white">
                            {BASES.map(b => <option key={b} value={b}>{b}</option>)}
                        </select>
                    </div>
                   <LeaderboardList data={topByBase} />
                </div>
                {/* By Fleet */}
                <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
                     <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xl font-semibold">By Fleet</h3>
                        <select value={filterFleet} onChange={e => setFilterFleet(e.target.value as Fleet)} className="bg-gray-700 border border-gray-600 rounded-md p-1 text-white">
                            {FLEETS.map(f => <option key={f} value={f}>{f}</option>)}
                        </select>
                    </div>
                    <LeaderboardList data={topByFleet} />
                </div>
            </div>
        </div>
    );
};

export default LeaderboardsPage;
