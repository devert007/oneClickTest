import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './Profile.css';

const Profile = () => {
    const { user, updateProfile } = useAuth();
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        name: user?.name || '',
        email: user?.email || '',
        password: '',
        confirmPassword: ''
    });
    const [message, setMessage] = useState('');

    const handleChange = (e) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setMessage('');

        if (formData.password && formData.password !== formData.confirmPassword) {
            setMessage('Пароли не совпадают');
            return;
        }

        if (formData.password && formData.password.length < 6) {
            setMessage('Пароль должен содержать минимум 6 символов');
            return;
        }

        // Обновляем профиль
        const updatedData = {
            name: formData.name,
            email: formData.email
        };

        if (formData.password) {
            updatedData.password = formData.password;
        }

        updateProfile(updatedData);
        setMessage('Профиль успешно обновлен!');
        setIsEditing(false);
        setFormData(prev => ({ ...prev, password: '', confirmPassword: '' }));
    };

    const handleCancel = () => {
        setIsEditing(false);
        setFormData({
            name: user?.name || '',
            email: user?.email || '',
            password: '',
            confirmPassword: ''
        });
        setMessage('');
    };

    return (
        <div className="profile-page">
            <div className="page-header">
                <h1>Профиль пользователя</h1>
                <p>Управляйте вашими персональными данными</p>
            </div>

            <div className="profile-content">
                <div className="profile-card">
                    <div className="profile-header">
                        <h3>Личная информация</h3>
                        {!isEditing && (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="btn btn-primary"
                            >
                                ✏️ Редактировать
                            </button>
                        )}
                    </div>

                    {message && (
                        <div className={`message ${message.includes('успешно') ? 'success' : 'error'}`}>
                            {message}
                        </div>
                    )}

                    {!isEditing ? (
                        <div className="profile-info">
                            <div className="info-item">
                                <label>Имя:</label>
                                <span>{user?.name || 'Не указано'}</span>
                            </div>
                            <div className="info-item">
                                <label>Email:</label>
                                <span>{user?.email || 'Не указан'}</span>
                            </div>
                            <div className="info-item">
                                <label>ID пользователя:</label>
                                <span>{user?.id || 'Не указан'}</span>
                            </div>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="profile-form">
                            <div className="form-group">
                                <label htmlFor="name">Имя</label>
                                <input
                                    type="text"
                                    id="name"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    placeholder="Введите ваше имя"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="email">Email</label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    placeholder="Введите ваш email"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="password">Новый пароль</label>
                                <input
                                    type="password"
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    placeholder="Оставьте пустым, если не хотите менять"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="confirmPassword">Подтвердите пароль</label>
                                <input
                                    type="password"
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    placeholder="Повторите новый пароль"
                                />
                            </div>

                            <div className="form-actions">
                                <button type="submit" className="btn btn-success">
                                    💾 Сохранить
                                </button>
                                <button
                                    type="button"
                                    onClick={handleCancel}
                                    className="btn btn-secondary"
                                >
                                    ❌ Отмена
                                </button>
                            </div>
                        </form>
                    )}
                </div>

                <div className="profile-stats">
                    <h3>Статистика аккаунта</h3>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <div className="stat-value">0</div>
                            <div className="stat-label">Загружено документов</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">0</div>
                            <div className="stat-label">Создано тестов</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">0</div>
                            <div className="stat-label">Активных сессий</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;