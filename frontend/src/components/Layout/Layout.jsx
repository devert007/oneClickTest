import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import HelpModal from '../Common/HelpModal';
import { HelpCircle } from 'lucide-react';
import './Layout.css';

const Layout = () => {
    const [showHelp, setShowHelp] = useState(false);
    const location = useLocation();

    const pageTitles = {
        '/': 'Главная',
        '/create-test': 'Генератор тестов',
        '/my-documents': 'Мои документы',
        '/my-tests': 'Мои тесты',
        '/chat': 'Чат с AI',
        '/profile': 'Профиль',
    };

    const currentTitle = pageTitles[location.pathname] || '';

    return (
        <div className="layout">
            <Sidebar />
            <div className="layout-body">
                {currentTitle && location.pathname !== '/' && (
                    <header className="layout-header">
                        <h2 className="header-title">{currentTitle}</h2>
                    </header>
                )}
                <main className="main-content">
                    <Outlet />
                </main>
            </div>

            <button
                className="help-button"
                onClick={() => setShowHelp(true)}
                title="Помощь"
            >
                <HelpCircle size={24} />
            </button>

            <HelpModal
                isOpen={showHelp}
                onClose={() => setShowHelp(false)}
            />
        </div>
    );
};

export default Layout;
