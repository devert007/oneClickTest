import React from 'react';
import PropTypes from 'prop-types';
import { X, FileText, Zap, FolderOpen, Download, MessageCircle } from 'lucide-react';
import './HelpModal.css';

const HelpModal = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    const sections = [
        {
            icon: <FileText size={20} />,
            title: 'Загрузка материалов',
            items: [
                'Поддержка форматов: PDF, DOCX',
                'Документы индексируются в векторную базу ChromaDB'
            ]
        },
        {
            icon: <Zap size={20} />,
            title: 'Генерация тестов',
            items: [
                'Настройка: количество вопросов, сложность, формат',
                'AI-модели для генерации',
                'Извлечение ключевых концепций из документов'
            ]
        },
        {
            icon: <FolderOpen size={20} />,
            title: 'Управление контентом',
            items: [
                'Просмотр истории документов',
                'Удаление материалов',
                'Архивация сгенерированных тестов'
            ]
        },
        {
            icon: <Download size={20} />,
            title: 'Экспорт результатов',
            items: [
                'Скачивание в Markdown и PDF',
                'Создание Google Форм',
                'Поддержка кириллицы'
            ]
        },
        {
            icon: <MessageCircle size={20} />,
            title: 'AI-чат',
            items: [
                'Вопросы по загруженным документам',
                'Сохранение истории чата',
                'RAG-поиск по контенту'
            ]
        }
    ];

    return (
        <div className="help-overlay" onClick={onClose}>
            <div className="help-modal" onClick={e => e.stopPropagation()}>
                <div className="help-modal-header">
                    <h2>О платформе</h2>
                    <button className="help-close" onClick={onClose}><X size={20} /></button>
                </div>

                <div className="help-modal-body">
                    <p className="help-intro">
                        <strong>OneClickTest</strong> — интеллектуальная платформа для автоматизации создания тестов
                        на основе учебных материалов с использованием AI.
                    </p>

                    <div className="help-sections">
                        {sections.map((s, i) => (
                            <div key={i} className="help-section">
                                <div className="help-section-icon">{s.icon}</div>
                                <div>
                                    <h4>{s.title}</h4>
                                    <ul>
                                        {s.items.map((item, j) => <li key={j}>{item}</li>)}
                                    </ul>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="help-modal-footer">
                    <button onClick={onClose} className="btn btn-primary">Закрыть</button>
                </div>
            </div>
        </div>
    );
};

HelpModal.propTypes = {
    isOpen: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired
};

export default HelpModal;
