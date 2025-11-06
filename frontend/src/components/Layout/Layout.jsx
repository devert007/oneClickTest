import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import HelpModal from '../Common/HelpModal';
import './Layout.css';

const Layout = () => {
    const [showHelp, setShowHelp] = useState(false);


    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content" >

                <Outlet />
            </main>

            {/* Кнопка помощи */}
            <button
                className="help-button"
                onClick={() => setShowHelp(true)}
                title="Помощь"
            >
                ?
            </button>

            <HelpModal
                isOpen={showHelp}
                onClose={() => setShowHelp(false)}
            />
        </div>
    );
};

export default Layout;