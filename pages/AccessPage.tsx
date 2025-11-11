
import React, { useState } from 'react';
import { ACCESS_CODE } from '../constants';

interface AccessPageProps {
    onAccessGranted: () => void;
}

const AccessPage: React.FC<AccessPageProps> = ({ onAccessGranted }) => {
    const [code, setCode] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (code === ACCESS_CODE) {
            onAccessGranted();
        } else {
            setError('Invalid code. Try again.');
            setCode('');
        }
    };

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-800 text-white p-4">
             <div className="text-center mb-8">
                <h1 className="text-5xl font-bold text-cyan-400">✈️ RateMyCaptain</h1>
                <p className="text-gray-400 mt-2">Built by FOs, for FOs.</p>
            </div>
            <div className="w-full max-w-sm p-8 bg-gray-900 rounded-lg shadow-2xl">
                <h2 className="text-2xl font-bold text-center mb-2">Crew Access Only</h2>
                <p className="text-center text-gray-400 mb-6">Enter access code to continue.</p>
                <form onSubmit={handleSubmit}>
                    <input
                        type="password"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        placeholder="Access Code"
                        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                    {error && <p className="text-red-500 text-sm mt-2 text-center">{error}</p>}
                    <button
                        type="submit"
                        className="w-full mt-6 bg-cyan-500 text-white font-bold py-2 px-4 rounded-md hover:bg-cyan-600 transition duration-300"
                    >
                        Unlock
                    </button>
                </form>
            </div>
            <p className="text-gray-600 text-xs mt-8">Not affiliated with any airline or management.</p>
        </div>
    );
};

export default AccessPage;
