import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './Sidebar.css';

const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const menuItems = [
        { path: '/create-test', label: 'Создать тест', icon: '📝' },
        { path: '/my-documents', label: 'Мои документы', icon: '📁' },
        { path: '/my-tests', label: 'Мои тесты', icon: '💾' },
        { path: '/profile', label: 'Профиль', icon: '👤' }
    ];

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <h2>OneClickTest</h2>
                {user && (
                    <div className="user-info">
                        <span>Привет, {user.name}!</span>
                    </div>
                )}
            </div>

            <nav className="sidebar-nav">
                {menuItems.map(item => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </Link>
                ))}
            </nav>

            <div className="sidebar-footer">
                <button onClick={handleLogout} className="logout-btn">
                    🚪 Выйти
                </button>
            </div>
        </div>
    );
};

export default Sidebar;