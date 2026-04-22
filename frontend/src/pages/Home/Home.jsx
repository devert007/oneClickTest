import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, FileText, MessageCircle, Shield, ArrowRight, Sparkles, BookOpen, ClipboardCheck } from 'lucide-react';
import './Home.css';

const Home = () => {
    const features = [
        {
            icon: <FileText size={28} />,
            title: 'Загрузка материалов',
            desc: 'Загружайте PDF и DOCX документы. Система автоматически индексирует их для интеллектуального анализа.'
        },
        {
            icon: <Zap size={28} />,
            title: 'AI-генерация тестов',
            desc: 'Настройте параметры и получите готовый тест за секунды. Множественный выбор или открытые вопросы.'
        },
        {
            icon: <MessageCircle size={28} />,
            title: 'Чат с AI',
            desc: 'Задавайте вопросы по загруженным документам и получайте точные ответы на основе RAG-технологий.'
        },
        {
            icon: <Shield size={28} />,
            title: 'Экспорт и интеграция',
            desc: 'Скачивайте тесты в PDF и Markdown, создавайте Google Формы одним кликом.'
        }
    ];

    return (
        <div className="home-page">
            <section className="hero">
                <div className="hero-glow" />
                <div className="hero-content">
                    <div className="hero-badge">
                        <Sparkles size={16} />
                        <span>AI-Powered Platform</span>
                    </div>
                    <h1>
                        Создавайте тесты <br />
                        <span className="hero-accent">в один клик</span>
                    </h1>
                    <p className="hero-subtitle">
                        Загрузите учебный материал, и OneClickTest автоматически сгенерирует
                        качественные тестовые задания с помощью искусственного интеллекта.
                    </p>
                    <div className="hero-actions">
                        <Link to="/create-test" className="btn btn-primary btn-lg">
                            <ClipboardCheck size={20} />
                            Создать тест
                            <ArrowRight size={18} />
                        </Link>
                        <Link to="/chat" className="btn btn-ghost btn-lg">
                            <MessageCircle size={20} />
                            Открыть чат
                        </Link>
                    </div>
                </div>
                <div className="hero-visual">
                    <div className="hero-card hero-card-1">
                        <BookOpen size={24} />
                        <span>Документы</span>
                    </div>
                    <div className="hero-card hero-card-2">
                        <Zap size={24} />
                        <span>AI Анализ</span>
                    </div>
                    <div className="hero-card hero-card-3">
                        <ClipboardCheck size={24} />
                        <span>Готовый тест</span>
                    </div>
                </div>
            </section>

            <section className="features">
                <h2 className="section-title">Возможности платформы</h2>
                <div className="features-grid">
                    {features.map((f, i) => (
                        <div key={i} className="feature-card">
                            <div className="feature-icon">{f.icon}</div>
                            <h3>{f.title}</h3>
                            <p>{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section className="stats-section">
                <div className="stat-block">
                    <span className="stat-num">PDF, DOCX</span>
                    <span className="stat-lbl">Форматы</span>
                </div>
                <div className="stat-divider" />
                <div className="stat-block">
                    <span className="stat-num">RAG + LLM</span>
                    <span className="stat-lbl">Технология</span>
                </div>
                <div className="stat-divider" />
                <div className="stat-block">
                    <span className="stat-num">1 клик</span>
                    <span className="stat-lbl">Генерация</span>
                </div>
            </section>
        </div>
    );
};

export default Home;
