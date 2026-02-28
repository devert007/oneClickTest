import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const AuthCallback = () => {
    const { loginWithToken } = useAuth();
    const [error, setError] = useState('');
    const processedRef = useRef(false);

    useEffect(() => {
        if (processedRef.current) return;

        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');

        if (!token) {
            setError('Отсутствует токен авторизации.');
            return;
        }

        processedRef.current = true;
        try {
            loginWithToken(token);
            window.location.replace('/');
        } catch (e) {
            processedRef.current = false;
            console.error('Ошибка при обработке токена авторизации:', e);
            setError('Некорректный токен авторизации.');
        }
    }, [loginWithToken]);

    if (error) {
        return (
            <div className="login-page">
                <div className="login-container">
                    <div className="login-header">
                        <h1>Ошибка авторизации</h1>
                    </div>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-header">
                    <h1>Завершение авторизации</h1>
                    <p>Пожалуйста, подождите...</p>
                </div>
            </div>
        </div>
    );
};

export default AuthCallback;

