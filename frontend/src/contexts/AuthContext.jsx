import React, { createContext, useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [authLoading, setAuthLoading] = useState(true); // Переименовали loading в authLoading

    useEffect(() => {
        // Проверка токена при загрузке
        const token = localStorage.getItem('token');
        if (token) {
            // Здесь можно добавить проверку токена на бэкенде
            setIsAuthenticated(true);
            const userData = localStorage.getItem('user');
            if (userData) {
                setUser(JSON.parse(userData));
            }
        }
        setAuthLoading(false);
    }, []);

    const register = (userData) => {
        // Заглушка для регистрации
        localStorage.setItem('token', 'fake-token');
        localStorage.setItem('user', JSON.stringify(userData));
        setIsAuthenticated(true);
        setUser(userData);
    };

    const login = (userData) => {
        // Заглушка для входа
        localStorage.setItem('token', 'fake-token');
        localStorage.setItem('user', JSON.stringify(userData));
        setIsAuthenticated(true);
        setUser(userData);
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setUser(null);
    };

    const value = {
        isAuthenticated,
        user,
        loading: authLoading, // Используем переименованную переменную
        register,
        login,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// Добавляем PropTypes для children
AuthProvider.propTypes = {
    children: PropTypes.node.isRequired
};

export default AuthContext;