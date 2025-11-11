import React, { useState } from 'react';
import FeedbackModal from './FeedbackModal';

const Footer: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    return (
        <>
            <footer className="w-full py-4 mt-8 text-center text-xs text-gray-500 border-t border-gray-700">
                <p>Not affiliated with any airline or management.</p>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="mt-2 text-cyan-400 hover:text-cyan-300 underline text-sm"
                >
                    Send Feedback
                </button>
            </footer>
            <FeedbackModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        </>
    );
};

export default Footer;