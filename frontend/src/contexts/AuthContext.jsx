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

    const register = (userData) => {
        localStorage.setItem('token', 'fake-token');
        localStorage.setItem('user', JSON.stringify(userData));
        setIsAuthenticated(true);
        setUser(userData);
    };

    const login = (userData) => {
        localStorage.setItem('token', 'fake-token');
        localStorage.setItem('user', JSON.stringify(userData));
        setIsAuthenticated(true);
        setUser(userData);
    };

    const loginWithToken = (token) => {
        try {
            localStorage.setItem('token', token);

            const payloadPart = token.split('.')[1];
            let parsedUser = null;
            if (payloadPart) {
                const decoded = JSON.parse(
                    atob(payloadPart.replace(/-/g, '+').replace(/_/g, '/'))
                );
                parsedUser = {
                    id: decoded.sub,
                    email: decoded.email,
                    name: decoded.name,
                    picture: decoded.picture,
                };
                localStorage.setItem('user', JSON.stringify(parsedUser));
            }

            setIsAuthenticated(true);
            setUser(parsedUser);
        } catch (e) {
            console.error('?????? ??????? JWT ??????:', e);
            // ? ?????? ?????? ??? ????? ??????? ???????????? ????????????????
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setIsAuthenticated(false);
            setUser(null);
            throw e;
        }
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
        loginWithToken,
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