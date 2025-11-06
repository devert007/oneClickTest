import React from 'react';
import PropTypes from 'prop-types';
import './HelpModal.css';

const HelpModal = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>OneClickTest - Справка</h2>
                    <button className="close-button" onClick={onClose}>×</button>
                </div>

                <div className="modal-body">
                    <div className="help-content">
                        <p>
                            <strong>OneClickTest</strong> - интеллектуальная платформа для автоматизированного создания тестов
                            на основе учебных материалов, с интеграцией AI и поддержкой полного цикла работы с контентом.
                        </p>

                        <h3>Основное назначение:</h3>
                        <p>
                            Автоматизация процесса создания тестовых заданий из загруженных документов (лекций, методичек, статей)
                            с использованием современных технологий AI (RAG-модели) и возможностью управления учебными материалами.
                        </p>

                        <h3>Ключевые функции:</h3>

                        <h4>Загрузка материалов</h4>
                        <ul>
                            <li>Поддержка форматов: PDF, DOCX</li>
                            <li>Документы индексируются в векторную базу ChromaDB для семантического поиска</li>
                        </ul>

                        <h4>Генерация тестов</h4>
                        <ul>
                            <li>Настройка параметров: количество вопросов, сложность, формат (множественный выбор/открытые вопросы)</li>
                            <li>Интеграция с AI-моделями (Llama3.2)</li>
                            <li>Автоматическое извлечение ключевых концепций из документов</li>
                        </ul>

                        <h4>Управление контентом</h4>
                        <ul>
                            <li>Просмотр истории загруженных документов</li>
                            <li>Удаление материалов</li>
                            <li>Архивация сгенерированных тестов</li>
                        </ul>

                        <h4>Экспорт результатов</h4>
                        <ul>
                            <li>Скачивание в форматах: Markdown, PDF</li>
                            <li>Автоматическое форматирование с поддержкой кириллицы</li>
                            <li>Генерация PDF с помощью ReportLab</li>
                        </ul>

                        <h4>Сессионная работа</h4>
                        <ul>
                            <li>Сохранение истории чата</li>
                            <li>Привязка тестов к сессиям и документам</li>
                            <li>Многопользовательская поддержка через систему session_id</li>
                        </ul>
                    </div>
                </div>

                <div className="modal-footer">
                    <button onClick={onClose} className="btn btn-primary">
                        Закрыть
                    </button>
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