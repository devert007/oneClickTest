import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './Login.css';

const Login = () => {
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Здесь будет интеграция с бэкендом
            // Пока используем заглушку
            const userData = {
                id: 1,
                name: 'Пользователь',
                email: formData.email
            };

            login(userData);
            navigate('/');
        } catch {
            setError('Ошибка входа. Проверьте email и пароль.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        setError('');
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/auth/google/login');
            if (!response.ok) {
                throw new Error('Не удалось получить ссылку для входа через Google');
            }
            const data = await response.json();
            if (!data.auth_url) {
                throw new Error('Некорректный ответ сервера авторизации');
            }
            window.location.href = data.auth_url;
        } catch (err) {
            console.error('Ошибка входа через Google:', err);
            setError(err.message || 'Ошибка входа через Google');
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-header">
                    <h1>OneClickTest</h1>
                    <p>Войдите в ваш аккаунт</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    {error && <div className="error-message">{error}</div>}

                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            placeholder="Введите ваш email"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Пароль</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            placeholder="Введите ваш пароль"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary login-btn"
                    >
                        {loading ? 'Вход...' : 'Войти'}
                    </button>

                    <button
                        type="button"
                        disabled={loading}
                        className="btn btn-secondary login-btn google-btn"
                        onClick={handleGoogleLogin}
                    >
                        {loading ? 'Переход к Google...' : 'Войти через Google'}
                    </button>
                </form>

                <div className="login-footer">
                    <p>
                        Нет аккаунта? <Link to="/register">Зарегистрируйтесь</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;