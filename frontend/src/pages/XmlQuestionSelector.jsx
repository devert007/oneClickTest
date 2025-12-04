import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { xmlAPI } from '../services/api';
import './XmlQuestionSelector.css';

const XmlQuestionSelector = ({
    selectedSubject,
    selectedTopic,
    selectedDifficulty,
    selectedQuestionType,
    questionCount,
    onSubjectChange,
    onTopicChange,
    onQuestionCountChange
}) => {
    const [subjects, setSubjects] = useState([]);
    const [topics, setTopics] = useState([]);
    const [availableQuestions, setAvailableQuestions] = useState(0);
    const [questionsPreview, setQuestionsPreview] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingPreview, setLoadingPreview] = useState(false);
    const [apiStatus, setApiStatus] = useState('checking');
    const [showPreview, setShowPreview] = useState(false);

    console.log('🔧 XmlQuestionSelector props:', {
        selectedSubject,
        selectedTopic,
        selectedDifficulty,
        selectedQuestionType,
        questionCount
    });

    // Загружаем предметы при монтировании
    useEffect(() => {
        loadSubjects();
    }, []);

    // Загружаем темы когда выбран предмет
    useEffect(() => {
        if (selectedSubject) {
            loadTopics(selectedSubject);
        } else {
            setTopics([]);
            setAvailableQuestions(0);
            setQuestionsPreview([]);
        }
    }, [selectedSubject]);

    // Обновляем количество доступных вопросов при изменении фильтров
    useEffect(() => {
        if (selectedSubject) {
            updateAvailableQuestions();
        }
    }, [selectedSubject, selectedTopic, selectedDifficulty, selectedQuestionType]);

    // Загружаем превью вопросов когда открыт предпросмотр
    useEffect(() => {
        if (showPreview && selectedSubject && availableQuestions > 0) {
            loadQuestionsPreview();
        } else {
            setQuestionsPreview([]);
        }
    }, [showPreview, selectedSubject, selectedTopic, selectedDifficulty, selectedQuestionType]);

    const loadSubjects = async () => {
        try {
            setLoading(true);
            setApiStatus('loading');
            console.log('🔄 Loading subjects from API...');

            const subjectsList = await xmlAPI.getSubjects();
            console.log('✅ API Subjects loaded:', subjectsList);

            if (subjectsList && subjectsList.length > 0) {
                setSubjects(subjectsList);
                setApiStatus('success');
            } else {
                setSubjects([]);
                setApiStatus('empty');
            }
        } catch (error) {
            console.error('❌ Error loading subjects:', error);
            setSubjects([]);
            setApiStatus('error');
        } finally {
            setLoading(false);
        }
    };

    const loadTopics = async (subject) => {
        try {
            setLoading(true);
            console.log(`🔄 Loading topics for: ${subject}`);

            const topicsList = await xmlAPI.getTopics(subject);
            console.log(`✅ API Topics for ${subject}:`, topicsList);

            setTopics(topicsList || []);
        } catch (error) {
            console.error(`❌ Error loading topics:`, error);
            setTopics([]);
        } finally {
            setLoading(false);
        }
    };

    const updateAvailableQuestions = async () => {
        if (selectedSubject) {
            try {
                console.log('🔄 Updating available questions with filters:', {
                    subject: selectedSubject,
                    topic: selectedTopic,
                    difficulty: selectedDifficulty,
                    questionType: selectedQuestionType
                });

                const count = await xmlAPI.getAvailableQuestionsCount(
                    selectedSubject,
                    selectedTopic,
                    selectedDifficulty,
                    selectedQuestionType
                );

                console.log(`✅ Available questions: ${count}`);
                setAvailableQuestions(count || 0);

                // Автоматически ограничиваем выбранное количество
                if (questionCount > count) {
                    onQuestionCountChange(Math.min(questionCount, count));
                }
            } catch (error) {
                console.error('❌ Error updating available questions:', error);
                setAvailableQuestions(0);
            }
        } else {
            setAvailableQuestions(0);
        }
    };

    // Функция для загрузки реальных вопросов из базы
    const loadQuestionsPreview = async () => {
        if (selectedSubject && availableQuestions > 0) {
            try {
                setLoadingPreview(true);
                console.log('📋 Loading real questions preview from API...');

                const realPreview = await xmlAPI.getQuestionsPreview(
                    selectedSubject,
                    selectedTopic,
                    selectedDifficulty,
                    selectedQuestionType,
                    3 // лимит для превью
                );

                console.log('✅ Real questions preview loaded:', realPreview);
                setQuestionsPreview(realPreview || []);
            } catch (error) {
                console.error('❌ Error loading real questions preview:', error);
                // В случае ошибки API, показываем информационное сообщение
                setQuestionsPreview([]);
            } finally {
                setLoadingPreview(false);
            }
        } else {
            setQuestionsPreview([]);
        }
    };

    const handleQuestionCountChange = (value) => {
        const numValue = parseInt(value) || 0;
        const limitedValue = Math.min(numValue, availableQuestions);
        console.log(`Setting question count to: ${limitedValue}`);
        onQuestionCountChange(limitedValue);
    };

    const handlePreviewToggle = () => {
        const newShowPreview = !showPreview;
        setShowPreview(newShowPreview);

        // Если открываем превью и еще не загружены вопросы, загружаем их
        if (newShowPreview && questionsPreview.length === 0 && selectedSubject && availableQuestions > 0) {
            loadQuestionsPreview();
        }
    };

    const getApiStatusMessage = () => {
        switch (apiStatus) {
            case 'loading':
                return '🔄 Загрузка данных с сервера...';
            case 'success':
                return `✅ База вопросов загружена (${subjects.length} предметов)`;
            case 'empty':
                return '📭 В базе нет доступных предметов';
            case 'error':
                return '❌ Ошибка загрузки базы вопросов';
            default:
                return '🔍 Проверка соединения...';
        }
    };

    return (
        <div className="xml-selector">
            <div className="xml-header">
                <h4>📚 Вопросы из базы данных</h4>
                {availableQuestions > 0 && (
                    <div className="xml-badge">
                        {availableQuestions} вопросов доступно
                    </div>
                )}
            </div>

            {/* Статус API */}
            <div className={`api-status ${apiStatus}`}>
                {getApiStatusMessage()}
            </div>

            {loading && (
                <div className="xml-loading">
                    <div className="loading-spinner"></div>
                    Загрузка данных...
                </div>
            )}

            <div className="xml-fields">
                <div className="form-group">
                    <label htmlFor="subject-select">
                        Предмет
                        <span className="required">*</span>
                    </label>
                    <select
                        id="subject-select"
                        value={selectedSubject || ''}
                        onChange={(e) => {
                            console.log('Subject changed to:', e.target.value);
                            onSubjectChange(e.target.value);
                        }}
                        className="form-control"
                        title="Выберите предмет из базы данных"
                        aria-label="Выберите предмет из базы данных"
                    >
                        <option value="">Выберите предмет...</option>
                        {subjects.map(subject => (
                            <option key={subject} value={subject}>
                                {subject}
                            </option>
                        ))}
                    </select>
                    <div className="field-info">
                        {subjects.length} предметов в базе
                    </div>
                </div>

                <div className="form-group">
                    <label htmlFor="topic-select">
                        Раздел
                        <span className="optional"> (опционально)</span>
                    </label>
                    <select
                        id="topic-select"
                        value={selectedTopic || ''}
                        onChange={(e) => {
                            console.log('Topic changed to:', e.target.value);
                            onTopicChange(e.target.value);
                        }}
                        className="form-control"
                        disabled={!selectedSubject || loading}
                        title="Выберите раздел предмета"
                        aria-label="Выберите раздел предмета"
                    >
                        <option value="">Все разделы</option>
                        {topics.map(topic => (
                            <option key={topic} value={topic}>
                                {topic}
                            </option>
                        ))}
                    </select>
                    <div className="field-info">
                        {topics.length} разделов доступно
                    </div>
                </div>

                <div className="form-group">
                    <label htmlFor="xml-question-count">
                        Количество вопросов
                        <span className="optional"> (макс: {availableQuestions})</span>
                    </label>
                    <input
                        id="xml-question-count"
                        type="number"
                        min="0"
                        max={availableQuestions}
                        value={questionCount}
                        onChange={(e) => handleQuestionCountChange(e.target.value)}
                        className="form-control"
                        disabled={!selectedSubject || availableQuestions === 0}
                        placeholder="Введите количество вопросов"
                        title="Количество вопросов для добавления из базы данных"
                        aria-label="Количество вопросов для добавления из базы данных"
                    />
                    <div className="question-counter">
                        <span>Выбрано: {questionCount}</span>
                        <span>Доступно: {availableQuestions}</span>
                    </div>
                </div>
            </div>

            {/* Кнопка предпросмотра */}
            {selectedSubject && availableQuestions > 0 && (
                <div className="preview-section">
                    <button
                        className="preview-toggle-btn"
                        onClick={handlePreviewToggle}
                        type="button"
                        disabled={loadingPreview}
                    >
                        {showPreview ? '▲ Скрыть вопросы из базы' : '▼ Показать вопросы из базы'}
                        {loadingPreview && ' (загрузка...)'}
                    </button>
                </div>
            )}

            {/* Превью бд вопросов */}
            {showPreview && (
                <div className="questions-preview">
                    <div className="preview-header">
                        <h5>📋 Ваши вопросы из базы:</h5>
                    </div>

                    <div className="preview-content">
                        {loadingPreview ? (
                            <div className="preview-loading">
                                <div className="loading-spinner small"></div>
                                Загрузка  вопросов...
                            </div>
                        ) : questionsPreview.length > 0 ? (
                            questionsPreview.map((question, index) => (
                                <div key={index} className="preview-item real-question">
                                    <div className="question-text">
                                        <strong>Вопрос {index + 1}:</strong> {question.question}
                                    </div>
                                    <div className="question-meta">
                                        <span className="meta-item">Тип: {question.type}</span>
                                        <span className="meta-item">Сложность: {question.difficulty}</span>
                                        <span className="meta-item">Предмет: {question.subject}</span>
                                        {question.topic && (
                                            <span className="meta-item">Раздел: {question.topic}</span>
                                        )}
                                        {question.answer && (
                                            <span className="meta-item answer">Ответ: {question.answer}</span>
                                        )}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="preview-no-questions">
                                <p>⚠️ Не удалось загрузить вопросы для предпросмотра</p>
                                <small>Проверьте подключение к серверу или настройки фильтров</small>
                            </div>
                        )}

                        {questionsPreview.length > 0 && (
                            <div className="preview-note">
                                <small>
                                    💡 Это <strong>вопросы</strong> из базы данных.
                                    При генерации теста будут добавлены эти вопросы.
                                </small>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {selectedSubject && availableQuestions === 0 && !loading && (
                <div className="xml-warning">
                    ⚠️ По выбранным параметрам вопросы не найдены. Попробуйте изменить фильтры.
                </div>
            )}

            {questionCount > 0 && (
                <div className="xml-success">
                    ✅ Будет добавлено {questionCount} вопросов из базы данных {selectedSubject}
                    {selectedTopic && ` (раздел: ${selectedTopic})`}
                </div>
            )}

            {/* Отладочная информация для разработки */}
            <div className="debug-info" style={{ display: 'none' }}>
                <strong>Отладка:</strong><br />
                Статус API: {apiStatus}<br />
                Предмет: {selectedSubject || 'не выбран'}<br />
                Раздел: {selectedTopic || 'не выбран'}<br />
                Сложность: {selectedDifficulty || 'не указана'}<br />
                Тип вопросов: {selectedQuestionType || 'не указан'}<br />
                Вопросов выбрано: {questionCount}<br />
                Доступно: {availableQuestions}<br />
                Превью загружено: {questionsPreview.length}
            </div>
        </div>
    );
};

// PropTypes
XmlQuestionSelector.propTypes = {
    selectedSubject: PropTypes.string,
    selectedTopic: PropTypes.string,
    selectedDifficulty: PropTypes.string,
    selectedQuestionType: PropTypes.string,
    questionCount: PropTypes.number,
    onSubjectChange: PropTypes.func.isRequired,
    onTopicChange: PropTypes.func.isRequired,
    onQuestionCountChange: PropTypes.func.isRequired
};

XmlQuestionSelector.defaultProps = {
    selectedSubject: '',
    selectedTopic: '',
    selectedDifficulty: '',
    selectedQuestionType: '',
    questionCount: 0
};

export default XmlQuestionSelector;