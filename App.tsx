import React, { useState, useEffect, useCallback } from 'react';
import type { Captain, Rating, Page } from './types';
import AccessPage from './pages/AccessPage';
import HomePage from './pages/HomePage';
import RateCaptainPage from './pages/RateCaptainPage';
import CaptainProfilePage from './pages/CaptainProfilePage';
import SearchPage from './pages/SearchPage';
import LeaderboardsPage from './pages/LeaderboardsPage';
import Header from './components/Header';
import Footer from './components/Footer';
import { loadData, saveData } from './api';


const App: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState<Page>('home');
    const [captains, setCaptains] = useState<Captain[]>([]);
    const [ratings, setRatings] = useState<Rating[]>([]);
    const [selectedCaptain, setSelectedCaptain] = useState<Captain | null>(null);
    const [prefilledCaptainName, setPrefilledCaptainName] = useState<string | null>(null);

    // Load data from the api service on initial mount
    useEffect(() => {
        const fetchData = async () => {
            const { captains: loadedCaptains, ratings: loadedRatings } = await loadData();
            setCaptains(loadedCaptains);
            setRatings(loadedRatings);
            setIsLoading(false);
        };
        fetchData();
    }, []);

    // Save data to the api service whenever it changes
    useEffect(() => {
        if (!isLoading) {
            saveData(captains, ratings);
        }
    }, [captains, ratings, isLoading]);

    useEffect(() => {
        if (currentPage !== 'rate' && prefilledCaptainName) {
            setPrefilledCaptainName(null);
        }
    }, [currentPage, prefilledCaptainName]);

    const handleAccessGranted = useCallback(() => {
        setIsAuthenticated(true);
    }, []);
    
    const handleNavigate = (page: Page) => {
        setCurrentPage(page);
    };

    const handleSelectCaptain = (captain: Captain) => {
        setSelectedCaptain(captain);
        setCurrentPage('profile');
    }

    const handleRateNewCaptain = (name: string) => {
        setPrefilledCaptainName(name);
        setCurrentPage('rate');
    };

    const handleAddRating = (newRating: Omit<Rating, 'id'>, captainInfo: Omit<Captain, 'id'>) => {
        let captainToUpdate: Captain | undefined = captains.find(c => c.id === newRating.captainId);

        if (!captainToUpdate) {
            // New captain
            const newCaptain: Captain = {
                id: newRating.captainId,
                ...captainInfo
            };
            setCaptains(prev => [...prev, newCaptain]);
        } else if (captainToUpdate.base !== captainInfo.base || captainToUpdate.fleet !== captainInfo.fleet) {
            // Update existing captain's info if it changed
            setCaptains(prev => prev.map(c => c.id === newRating.captainId ? {...c, ...captainInfo} : c));
        }

        setRatings(prev => [...prev, { id: `r_${Date.now()}`, ...newRating }]);
        alert('Rating submitted successfully! Thank you for your feedback.');
    };

    const renderPage = () => {
        switch (currentPage) {
            case 'rate':
                return <RateCaptainPage captains={captains} onAddRating={handleAddRating} onFinish={() => setCurrentPage('home')} initialName={prefilledCaptainName || undefined} />;
            case 'search':
                return <SearchPage captains={captains} onSelectCaptain={handleSelectCaptain} onRateNewCaptain={handleRateNewCaptain} />;
            case 'profile':
                return selectedCaptain ? <CaptainProfilePage captain={selectedCaptain} ratings={ratings} /> : <HomePage captains={captains} ratings={ratings} onSelectCaptain={handleSelectCaptain} onRateNewCaptain={handleRateNewCaptain} />;
            case 'leaderboards':
                return <LeaderboardsPage captains={captains} ratings={ratings} onSelectCaptain={handleSelectCaptain} />;
            case 'home':
            default:
                return <HomePage captains={captains} ratings={ratings} onSelectCaptain={handleSelectCaptain} onRateNewCaptain={handleRateNewCaptain} />;
        }
    }

    if (!isAuthenticated) {
        return <AccessPage onAccessGranted={handleAccessGranted} />;
    }

    if (isLoading) {
        return (
             <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 text-white">
                <h1 className="text-3xl font-bold text-cyan-400">✈️ RateMyCaptain</h1>
                <p className="mt-4 text-gray-400">Loading data...</p>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex flex-col bg-gray-900 text-gray-100">
            <Header onNavigate={handleNavigate} />
            <main className="flex-grow">
                {renderPage()}
            </main>
            <Footer />
        </div>
    );
};

export default App;