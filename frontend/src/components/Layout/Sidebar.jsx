import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Home, ClipboardCheck, FolderOpen, Archive, MessageCircle, User, LogOut } from 'lucide-react';
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
        { path: '/', label: 'Главная', icon: <Home size={20} /> },
        { path: '/create-test', label: 'Создать тест', icon: <ClipboardCheck size={20} /> },
        { path: '/my-documents', label: 'Мои документы', icon: <FolderOpen size={20} /> },
        { path: '/my-tests', label: 'Мои тесты', icon: <Archive size={20} /> },
        { path: '/chat', label: 'Чат с AI', icon: <MessageCircle size={20} /> },
        { path: '/profile', label: 'Профиль', icon: <User size={20} /> }
    ];

    const isActive = (path) => {
        if (path === '/') return location.pathname === '/';
        return location.pathname.startsWith(path);
    };

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="brand-icon">
                    <ClipboardCheck size={22} />
                </div>
                <span className="brand-text">OneClickTest</span>
            </div>

            {user && (
                <div className="sidebar-user">
                    <div className="user-avatar">
                        {user.name?.charAt(0)?.toUpperCase() || 'U'}
                    </div>
                    <span className="user-name">{user.name}</span>
                </div>
            )}

            <nav className="sidebar-nav">
                {menuItems.map(item => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </Link>
                ))}
            </nav>

            <div className="sidebar-footer">
                <button onClick={handleLogout} className="logout-btn">
                    <LogOut size={18} />
                    <span>Выйти</span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
