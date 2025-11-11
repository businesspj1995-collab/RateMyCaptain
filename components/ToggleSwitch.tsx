
import React from 'react';

interface ToggleSwitchProps {
    label: string;
    description: string;
    value: boolean;
    onChange: (value: boolean) => void;
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({ label, description, value, onChange }) => {
    const toggle = () => onChange(!value);

    return (
        <div className="py-4 flex justify-between items-center">
            <div>
                <span className="font-semibold text-lg text-gray-100">{label}</span>
                <p className="text-sm text-gray-400">{description}</p>
            </div>
            <div className="flex items-center space-x-3">
                <span className={`font-semibold ${!value ? 'text-cyan-400' : 'text-gray-500'}`}>No</span>
                <button
                    type="button"
                    onClick={toggle}
                    className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors ${value ? 'bg-cyan-500' : 'bg-gray-600'}`}
                >
                    <span
                        className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform ${value ? 'translate-x-6' : 'translate-x-1'}`}
                    />
                </button>
                <span className={`font-semibold ${value ? 'text-cyan-400' : 'text-gray-500'}`}>Yes</span>
            </div>
        </div>
    );
};

export default ToggleSwitch;
