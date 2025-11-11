
import React, { useMemo, useState } from 'react';
import type { Captain, Rating } from '../types';
import { RATING_CATEGORIES } from '../constants';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend } from 'recharts';

interface CaptainProfilePageProps {
    captain: Captain;
    ratings: Rating[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="p-2 bg-gray-700 border border-gray-600 rounded-md">
          <p className="label text-white">{`${label} : ${payload[0].value.toFixed(1)}`}</p>
        </div>
      );
    }
    return null;
  };

const CaptainProfilePage: React.FC<CaptainProfilePageProps> = ({ captain, ratings }) => {
    const [chartType, setChartType] = useState<'bar' | 'radar'>('bar');

    const captainRatings = useMemo(() => ratings.filter(r => r.captainId === captain.id), [captain.id, ratings]);

    const aggregatedData = useMemo(() => {
        if (captainRatings.length === 0) return null;

        const data: { [key: string]: number | string } = {};
        const chartData: { name: string, score: number, fullMark: number }[] = [];

        let totalScore = 0;
        let scoredItemsCount = 0;

        Object.entries(RATING_CATEGORIES).forEach(([key, config]) => {
            const ratingKey = key as keyof Rating;
            if (config.type === 'scale') {
                const avg = captainRatings.reduce((acc, r) => acc + (r[ratingKey] as number), 0) / captainRatings.length;
                data[key] = parseFloat(avg.toFixed(1));
                if (key !== 'socialInteraction' && key !== 'mentorship') {
                    chartData.push({ name: config.label.split(' ')[0], score: avg, fullMark: 5 });
                }
                if (config.scored) {
                    totalScore += avg;
                    scoredItemsCount++;
                }
            } else { // toggle
                const yesCount = captainRatings.filter(r => r[ratingKey] === true).length;
                const percentage = (yesCount / captainRatings.length) * 100;
                data[key] = parseFloat(percentage.toFixed(0));
                if (config.scored) {
                    totalScore += percentage / 20; // Normalize to a 5-point scale
                    scoredItemsCount++;
                }
            }
        });
        
        data.overall = parseFloat((totalScore / scoredItemsCount).toFixed(1));
        const wouldFlyAgainAvg = captainRatings.reduce((acc, r) => acc + r.wouldFlyAgain, 0) / captainRatings.length;
        data.wouldFlyAgainPercent = parseFloat(((wouldFlyAgainAvg/5) * 100).toFixed(0));

        return { scores: data, chartData };
    }, [captainRatings]);

    if (captainRatings.length === 0 || !aggregatedData) {
        return (
            <div className="p-4 md:p-8 text-center">
                <h2 className="text-3xl font-bold">{captain.name}</h2>
                <p className="text-gray-400">{captain.base} • {captain.fleet}</p>
                <p className="mt-8 text-lg">No ratings found for this captain yet.</p>
            </div>
        );
    }

    const { scores, chartData } = aggregatedData;

    const getBarColor = (value: number) => {
        if (value >= 4) return "#22c55e"; // green-500
        if (value >= 3) return "#eab308"; // yellow-500
        return "#ef4444"; // red-500
    };

    return (
        <div className="p-4 md:p-8 max-w-5xl mx-auto">
            <div className="text-center mb-8">
                <h2 className="text-4xl font-bold">{captain.name}</h2>
                <p className="text-lg text-gray-400">{captain.base} • {captain.fleet}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                 <div className="bg-gray-800 p-6 rounded-lg text-center flex flex-col justify-center items-center">
                    <p className="text-gray-400 text-sm">OVERALL SCORE</p>
                    <p className="text-6xl font-bold text-cyan-400">{scores.overall}</p>
                 </div>
                 <div className="bg-gray-800 p-6 rounded-lg text-center flex flex-col justify-center items-center">
                    <p className="text-gray-400 text-sm">WOULD FLY AGAIN</p>
                    <p className="text-6xl font-bold text-cyan-400">{scores.wouldFlyAgainPercent}%</p>
                 </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-gray-800 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4 text-cyan-400">Detailed Scores</h3>
                    <div className="space-y-3">
                        {Object.entries(RATING_CATEGORIES).map(([key, config]) => (
                            <div key={key} className="flex justify-between items-center text-lg">
                                <span className="text-gray-300">{config.label}</span>
                                <span className={`font-bold ${config.scored ? 'text-white' : 'text-gray-500'}`}>
                                    {scores[key]} {config.type === 'toggle' ? '%' : ''}
                                    {!config.scored && <span className="text-xs"> (not scored)</span>}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-gray-800 p-6 rounded-lg">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xl font-semibold text-cyan-400">Ratings Chart</h3>
                        <div className="flex items-center space-x-2 bg-gray-700 p-1 rounded-md">
                            <button onClick={() => setChartType('bar')} className={`px-2 py-1 text-sm rounded ${chartType === 'bar' ? 'bg-cyan-500 text-white' : 'text-gray-300'}`}>Bar</button>
                            <button onClick={() => setChartType('radar')} className={`px-2 py-1 text-sm rounded ${chartType === 'radar' ? 'bg-cyan-500 text-white' : 'text-gray-300'}`}>Radar</button>
                        </div>
                    </div>
                    <div className="w-full h-80">
                        <ResponsiveContainer>
                            {chartType === 'bar' ? (
                                <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 20, left: 50, bottom: 5 }}>
                                    <XAxis type="number" domain={[1, 5]} hide />
                                    <YAxis type="category" dataKey="name" stroke="#9ca3af" width={100} interval={0} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}/>
                                    <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                                        {chartData.map((entry, index) => (
                                            <svg key={`cell-${index}`} fill={getBarColor(entry.score)} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            ) : (
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                                    <PolarGrid stroke="#4b5563"/>
                                    <PolarAngleAxis dataKey="name" stroke="#9ca3af"/>
                                    <PolarRadiusAxis angle={30} domain={[1, 5]} tick={false} axisLine={false} />
                                    <Radar name="Score" dataKey="score" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.6} />
                                    <Tooltip content={<CustomTooltip />} />
                                </RadarChart>
                            )}
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CaptainProfilePage;
