import React from 'react';
import { SCALE_GUIDE } from '../constants';

interface RatingSliderProps {
    label: string;
    description: string;
    value: number;
    onChange: (value: number) => void;
    scaleGuide?: { [key: number]: string };
}

const RatingSlider: React.FC<RatingSliderProps> = ({ label, description, value, onChange, scaleGuide }) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(parseInt(e.target.value, 10));
    };

    const currentScaleGuide = scaleGuide || SCALE_GUIDE;

    return (
        <div className="py-4">
            <label className="block mb-2">
                <span className="font-semibold text-lg text-gray-100">{label}</span>
                <p className="text-sm text-gray-400">{description}</p>
            </label>
            <div className="flex items-center space-x-4">
                <input
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    value={value}
                    onChange={handleChange}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
                <div className="w-40 text-center">
                    <span className="text-2xl font-bold text-cyan-400">{value}</span>
                    <p className="text-xs text-gray-400 h-8 flex items-center justify-center">{currentScaleGuide[value]}</p>
                </div>
            </div>
        </div>
    );
};

export default RatingSlider;
