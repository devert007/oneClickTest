import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Save, X, Edit3, User, Mail, Hash } from 'lucide-react';
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
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setMessage('');

        if (formData.password && formData.password !== formData.confirmPassword) {
            setMessage('Пароли не совпадают');
            return;
        }
        if (formData.password && formData.password.length < 6) {
            setMessage('Пароль: минимум 6 символов');
            return;
        }

        const updatedData = { name: formData.name, email: formData.email };
        if (formData.password) updatedData.password = formData.password;

        updateProfile(updatedData);
        setMessage('Профиль обновлён!');
        setIsEditing(false);
        setFormData(prev => ({ ...prev, password: '', confirmPassword: '' }));
    };

    const handleCancel = () => {
        setIsEditing(false);
        setFormData({ name: user?.name || '', email: user?.email || '', password: '', confirmPassword: '' });
        setMessage('');
    };

    return (
        <div className="profile-page">
            <div className="profile-card">
                <div className="profile-card-header">
                    <h3>Личная информация</h3>
                    {!isEditing && (
                        <button onClick={() => setIsEditing(true)} className="btn btn-primary btn-sm">
                            <Edit3 size={14} /> Редактировать
                        </button>
                    )}
                </div>

                {message && (
                    <div className={`profile-msg ${message.includes('обновлён') ? 'success' : 'error'}`}>
                        {message}
                    </div>
                )}

                {!isEditing ? (
                    <div className="profile-info-list">
                        <div className="profile-info-row">
                            <div className="profile-info-icon"><User size={18} /></div>
                            <div>
                                <span className="profile-label">Имя</span>
                                <span className="profile-value">{user?.name || 'Не указано'}</span>
                            </div>
                        </div>
                        <div className="profile-info-row">
                            <div className="profile-info-icon"><Mail size={18} /></div>
                            <div>
                                <span className="profile-label">Email</span>
                                <span className="profile-value">{user?.email || 'Не указан'}</span>
                            </div>
                        </div>
                        <div className="profile-info-row">
                            <div className="profile-info-icon"><Hash size={18} /></div>
                            <div>
                                <span className="profile-label">ID</span>
                                <span className="profile-value">{user?.id || '—'}</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="profile-form">
                        <div className="form-group">
                            <label htmlFor="name">Имя</label>
                            <input type="text" id="name" name="name" value={formData.name} onChange={handleChange} placeholder="Имя" className="form-control" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="email">Email</label>
                            <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} placeholder="Email" className="form-control" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="password">Новый пароль</label>
                            <input type="password" id="password" name="password" value={formData.password} onChange={handleChange} placeholder="Оставьте пустым" className="form-control" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="confirmPassword">Подтвердите пароль</label>
                            <input type="password" id="confirmPassword" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} placeholder="Повторите" className="form-control" />
                        </div>
                        <div className="profile-form-actions">
                            <button type="submit" className="btn btn-primary">
                                <Save size={16} /> Сохранить
                            </button>
                            <button type="button" onClick={handleCancel} className="btn btn-secondary">
                                <X size={16} /> Отмена
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
};

export default Profile;
