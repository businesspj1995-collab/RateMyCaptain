
import React from 'react';
import type { Page } from '../types';

interface HeaderProps {
    onNavigate: (page: Page) => void;
}

const Header: React.FC<HeaderProps> = ({ onNavigate }) => {
    return (
        <header className="w-full p-4 bg-gray-800/50 backdrop-blur-sm border-b border-gray-700 flex justify-between items-center">
            <h1 
                className="text-2xl font-bold text-cyan-400 cursor-pointer"
                onClick={() => onNavigate('home')}
            >
                ✈️ RateMyCaptain
            </h1>
            <nav className="flex items-center">
                <button onClick={() => onNavigate('leaderboards')} className="text-gray-300 hover:text-cyan-400 transition">Leaderboards</button>
            </nav>
        </header>
    );
};

export default Header;