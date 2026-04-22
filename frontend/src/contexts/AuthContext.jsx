import React, { createContext, useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import { authAPI } from '../services/api';

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
    const [authLoading, setAuthLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            setIsAuthenticated(true);
            const userData = localStorage.getItem('user');
            if (userData) {
                setUser(JSON.parse(userData));
            }
        }
        setAuthLoading(false);
    }, []);

    const register = async ({ email, name }) => {
        const { token, user: serverUser } = await authAPI.emailLogin(email, name);
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(serverUser));
        setIsAuthenticated(true);
        setUser(serverUser);
    };

    const login = async ({ email, name }) => {
        const { token, user: serverUser } = await authAPI.emailLogin(email, name);
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(serverUser));
        setIsAuthenticated(true);
        setUser(serverUser);
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
        loading: authLoading,
        register,
        login,
        logout,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// ��������� PropTypes ��� children
AuthProvider.propTypes = {
    children: PropTypes.node.isRequired
};

export default AuthContext;