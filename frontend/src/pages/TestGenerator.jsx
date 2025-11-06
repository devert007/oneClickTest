import React, { useState, useEffect } from 'react';
import { documentAPI, testGenerationAPI, testPDFAPI } from '../services/api';
import XmlQuestionSelector from './XmlQuestionSelector';
import './TestGenerator.css';

const TestGenerator = () => {
    const [documents, setDocuments] = useState([]);
    const [selectedDocument, setSelectedDocument] = useState('');
    const [testParams, setTestParams] = useState({
        questionCount: 10,
        difficulty: 'Для средних классов',
        questionType: 'multiple_choice',
        includeAnswers: true,
        model: 'llama3.2',
        // XML параметры
        xmlSubject: '',
        xmlTopic: '',
        xmlQuestionCount: 0,
        availableXmlQuestions: 0
    });
    const [generatedTest, setGeneratedTest] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [savedTests, setSavedTests] = useState([]);
    const [activeTab, setActiveTab] = useState('generate');

    const difficultyLevels = [
        { value: 'Для начальных классов', label: '🟢 Для начальных классов' },
        { value: 'Для средних классов', label: '🟡 Для средних классов' },
        { value: 'Для старших классов', label: '🔴 Для старших классов' },
        { value: 'Для студентов', label: '🎓 Для студентов' }
    ];

    const questionTypes = [
        { value: 'multiple_choice', label: '📋 С выбором ответа' },
        { value: 'open_questions', label: '📝 Открытые вопросы' }
    ];

    const models = [
        { value: 'llama3.2', label: '🦙 Llama 3.2' }
    ];

    useEffect(() => {
        console.log('🏁 TestGenerator mounted, loading data...');
        loadDocuments();
        loadSavedTests();
    }, []);

    const loadDocuments = async () => {
        try {
            const docs = await documentAPI.getDocuments();
            setDocuments(docs);
        } catch (error) {
            console.error('Error loading documents:', error);
            alert(`Ошибка при загрузке документов: ${error.message}`);
        }
    };

    const loadSavedTests = async () => {
        try {
            const tests = await testPDFAPI.getTestPDFs();
            setSavedTests(tests);
        } catch (error) {
            console.error('Error loading saved tests:', error);
        }
    };

    const generateTest = async () => {
        if (!selectedDocument && testParams.xmlQuestionCount === 0) {
            alert('Пожалуйста, выберите документ или добавьте вопросы из базы данных');
            return;
        }

        if (testParams.xmlQuestionCount > testParams.questionCount) {
            alert('Количество вопросов из базы не может превышать общее количество вопросов');
            return;
        }

        setIsGenerating(true);
        setGeneratedTest(null);

        try {
            const requestData = {
                question_count: testParams.questionCount,
                difficulty: testParams.difficulty,
                question_type: testParams.questionType,
                include_answers: testParams.includeAnswers,
                model: testParams.model,
                xml_subject: testParams.xmlSubject || null,
                xml_topic: testParams.xmlTopic || null,
                xml_question_count: testParams.xmlQuestionCount,
                session_id: `session_${Date.now()}`
            };

            if (selectedDocument) {
                requestData.document_id = parseInt(selectedDocument);
            }

            console.log('📤 Sending request data:', requestData);

            const result = await testGenerationAPI.generateTest(requestData);
            console.log('📥 Received result:', result);

            setGeneratedTest(result);

            if (result.parameters) {
                console.log(`Statistics: ${result.parameters.xml_question_count} XML questions, ${result.parameters.ai_question_count} AI questions`);
            }
        } catch (error) {
            console.error('Error generating test:', error);
            alert(`Ошибка при генерации теста: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    };

    const saveTest = async () => {
        if (!generatedTest) return;

        try {
            const filename = `test_${Date.now()}.md`;
            const documentId = selectedDocument ? parseInt(selectedDocument) : null;

            await testGenerationAPI.saveTest(
                generatedTest.test_content,
                filename,
                documentId,
                generatedTest.session_id
            );

            alert('Тест успешно сохранен!');
            await loadSavedTests();
            setActiveTab('saved');
        } catch (error) {
            console.error('Error saving test:', error);
            alert(`Ошибка при сохранении теста: ${error.message}`);
        }
    };

    const downloadTest = (testContent, filename = `test_${Date.now()}.md`) => {
        const blob = new Blob([testContent], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const deleteTest = async (testId, filename) => {
        if (!confirm(`Удалить тест "${filename}"?`)) return;

        try {
            await testPDFAPI.deleteTestPDF(testId);
            await loadSavedTests();
            alert('Тест удален');
        } catch (error) {
            console.error('Error deleting test:', error);
            alert(`Ошибка при удалении теста: ${error.message}`);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('ru-RU');
    };

    const getDocumentName = (documentId) => {
        const doc = documents.find(d => d.id === documentId);
        return doc ? doc.filename : 'Не указан';
    };

    return (
    <div className="test-generator">
        
        <div className="xml-integrated-section" style={{
            border: '3px solid green',
            padding: '20px',
            margin: '20px 0',
            background: '#f0fff0'
        }}>
            <h3 style={{ color: 'green', marginTop: 0 }}>✅ ИНТЕГРИРОВАННАЯ XML СЕКЦИЯ</h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
                <div>
                    <label><strong>Предмет из базы:</strong></label>
                    <select
                        value={testParams.xmlSubject}
                        onChange={(e) => setTestParams(prev => ({ ...prev, xmlSubject: e.target.value }))}
                        style={{ width: '100%', padding: '10px' }}
                    >
                        <option value="">Выберите предмет...</option>
                        <option value="Математика">Математика</option>
                        <option value="Физика">Физика</option>
                    </select>
                </div>

                <div>
                    <label><strong>Раздел:</strong></label>
                    <select
                        value={testParams.xmlTopic}
                        onChange={(e) => setTestParams(prev => ({ ...prev, xmlTopic: e.target.value }))}
                        style={{ width: '100%', padding: '10px' }}
                        disabled={!testParams.xmlSubject}
                    >
                        <option value="">Все разделы</option>
                        <option value="Алгебра">Алгебра</option>
                        <option value="Геометрия">Геометрия</option>
                    </select>
                </div>

                <div>
                    <label><strong>Количество вопросов:</strong></label>
                    <input
                        type="number"
                        min="0"
                        max="20"
                        value={testParams.xmlQuestionCount}
                        onChange={(e) => setTestParams(prev => ({ ...prev, xmlQuestionCount: parseInt(e.target.value) || 0 }))}
                        style={{ width: '100%', padding: '10px' }}
                        placeholder="0-20"
                    />
                </div>
            </div>

            <div style={{
                marginTop: '15px',
                padding: '15px',
                background: testParams.xmlQuestionCount > 0 ? '#d4edda' : '#fff3cd',
                borderRadius: '5px'
            }}>
                {testParams.xmlQuestionCount > 0 ? (
                    <span style={{ color: '#155724' }}>
                        ✅ Будет добавлено {testParams.xmlQuestionCount} вопросов из базы данных
                    </span>
                ) : (
                    <span style={{ color: '#856404' }}>
                        ℹ️ Выберите предмет и количество вопросов для добавления из базы
                    </span>
                )}
            </div>
        </div>
        <h2>Генератор тестов</h2>
        <div className="test-generator">
            <h2>Генератор тестов</h2>

            <div className="tabs">
                <button
                    className={`tab ${activeTab === 'generate' ? 'active' : ''}`}
                    onClick={() => setActiveTab('generate')}
                    title="Перейти к генерации теста"
                    aria-label="Перейти к генерации теста"
                >
                    📝 Генерация теста
                </button>
                <button
                    className={`tab ${activeTab === 'saved' ? 'active' : ''}`}
                    onClick={() => setActiveTab('saved')}
                    title="Просмотреть сохраненные тесты"
                    aria-label="Просмотреть сохраненные тесты"
                >
                    💾 Сохраненные тесты ({savedTests.length})
                </button>
            </div>

            {activeTab === 'generate' && (
                <>
                    <div className="params-panel card">
                        <h3>Основные параметры теста</h3>

                        <div className="params-grid">
                            <div className="form-group">
                                <label htmlFor="document-select">Документ для тестирования:</label>
                                <select
                                    id="document-select"
                                    value={selectedDocument}
                                    onChange={(e) => setSelectedDocument(e.target.value)}
                                    className="form-control"
                                    title="Выберите документ для генерации теста"
                                    aria-label="Выберите документ для генерации теста"
                                >
                                    <option value="">Выберите документ...</option>
                                    {documents.map(doc => (
                                        <option key={doc.id} value={doc.id}>
                                            {doc.filename} (ID: {doc.id})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="total-question-count">Общее количество вопросов:</label>
                                <input
                                    id="total-question-count"
                                    type="number"
                                    min="1"
                                    max="50"
                                    value={testParams.questionCount}
                                    onChange={(e) => setTestParams(prev => ({
                                        ...prev,
                                        questionCount: parseInt(e.target.value)
                                    }))}
                                    className="form-control"
                                    title="Общее количество вопросов в тесте от 1 до 50"
                                    aria-label="Общее количество вопросов в тесте"
                                    placeholder="Введите число от 1 до 50"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="difficulty-select">Сложность:</label>
                                <select
                                    id="difficulty-select"
                                    value={testParams.difficulty}
                                    onChange={(e) => setTestParams(prev => ({
                                        ...prev,
                                        difficulty: e.target.value
                                    }))}
                                    className="form-control"
                                    title="Уровень сложности теста"
                                    aria-label="Выберите уровень сложности теста"
                                >
                                    {difficultyLevels.map(level => (
                                        <option key={level.value} value={level.value}>
                                            {level.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="question-type-select">Тип вопросов:</label>
                                <select
                                    id="question-type-select"
                                    value={testParams.questionType}
                                    onChange={(e) => setTestParams(prev => ({
                                        ...prev,
                                        questionType: e.target.value
                                    }))}
                                    className="form-control"
                                    title="Тип генерируемых вопросов"
                                    aria-label="Выберите тип вопросов"
                                >
                                    {questionTypes.map(type => (
                                        <option key={type.value} value={type.value}>
                                            {type.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="model-select">AI Модель:</label>
                                <select
                                    id="model-select"
                                    value={testParams.model}
                                    onChange={(e) => setTestParams(prev => ({
                                        ...prev,
                                        model: e.target.value
                                    }))}
                                    className="form-control"
                                    title="Модель ИИ для генерации вопросов"
                                    aria-label="Выберите модель искусственного интеллекта"
                                >
                                    {models.map(model => (
                                        <option key={model.value} value={model.value}>
                                            {model.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        
                        {/* Секция XML вопросов */}
                        <div className="xml-section" style={{ border: '3px solid red', padding: '20px', margin: '20px 0' }}>
                            <h2 style={{ color: 'red' }}>🚨 XML СЕКЦИЯ - ДОЛЖНА БЫТЬ ВИДИМА</h2>

                            <div style={{ background: 'yellow', padding: '10px', marginBottom: '15px' }}>
                                <strong>Параметры XML:</strong><br />
                                Subject: {testParams.xmlSubject || 'не выбран'}<br />
                                Topic: {testParams.xmlTopic || 'не выбран'}<br />
                                Question Count: {testParams.xmlQuestionCount}
                            </div>

                            <XmlQuestionSelector
                                selectedSubject={testParams.xmlSubject}
                                selectedTopic={testParams.xmlTopic}
                                selectedDifficulty={testParams.difficulty}
                                selectedQuestionType={testParams.questionType}
                                questionCount={testParams.xmlQuestionCount}
                                onSubjectChange={(subject) => {
                                    console.log('Subject changed in TestGenerator:', subject);
                                    setTestParams(prev => ({
                                        ...prev,
                                        xmlSubject: subject,
                                        xmlTopic: '' // Сбрасываем тему
                                    }));
                                }}
                                onTopicChange={(topic) => {
                                    console.log('Topic changed in TestGenerator:', topic);
                                    setTestParams(prev => ({
                                        ...prev,
                                        xmlTopic: topic
                                    }));
                                }}
                                onQuestionCountChange={(count) => {
                                    console.log('Question count changed in TestGenerator:', count);
                                    setTestParams(prev => ({
                                        ...prev,
                                        xmlQuestionCount: count
                                    }));
                                }}
                            />
                        </div>

                        <div className="form-check">
                            <input
                                type="checkbox"
                                checked={testParams.includeAnswers}
                                onChange={(e) => setTestParams(prev => ({
                                    ...prev,
                                    includeAnswers: e.target.checked
                                }))}
                                className="form-check-input"
                                id="includeAnswers"
                                title="Включать ответы в тест"
                                aria-label="Включать ответы в тест"
                            />
                            <label htmlFor="includeAnswers" className="form-check-label">
                                Включать ответы
                            </label>
                        </div>

                        <button
                            onClick={generateTest}
                            disabled={isGenerating || (!selectedDocument && testParams.xmlQuestionCount === 0)}
                            className="btn btn-primary generate-btn"
                            title="Сгенерировать тест с выбранными параметрами"
                            aria-label="Сгенерировать тест"
                        >
                            {isGenerating ? '🔄 Генерация...' : '⚡ Сгенерировать тест'}
                        </button>

                        {documents.length === 0 && testParams.xmlQuestionCount === 0 && (
                            <div className="warning-message">
                                ⚠️ Для генерации тестов необходимо загрузить документы или выбрать вопросы из базы данных
                            </div>
                        )}
                    </div>

                    {generatedTest && (
                        <div className="test-result card">
                            <div className="result-header">
                                <h3>Сгенерированный тест</h3>
                                <div className="result-stats">
                                    <p>
                                        📊 Всего вопросов: {generatedTest.parameters.question_count}
                                        {generatedTest.parameters.xml_question_count > 0 &&
                                            ` (${generatedTest.parameters.xml_question_count} из базы, ${generatedTest.parameters.ai_question_count} сгенерировано)`}
                                    </p>
                                </div>
                                <div className="result-actions">
                                    <button
                                        onClick={saveTest}
                                        className="btn btn-success"
                                        title="Сохранить тест в базу данных"
                                        aria-label="Сохранить тест"
                                    >
                                        💾 Сохранить тест
                                    </button>
                                    <button
                                        onClick={() => downloadTest(generatedTest.test_content)}
                                        className="btn btn-secondary"
                                        title="Скачать тест в формате Markdown"
                                        aria-label="Скачать тест"
                                    >
                                        📥 Скачать Markdown
                                    </button>
                                </div>
                            </div>

                            <div className="test-content">
                                <pre>{generatedTest.test_content}</pre>
                            </div>
                        </div>
                    )}
                </>
            )}

            {activeTab === 'saved' && (
                <div className="saved-tests card">
                    <div className="tests-header">
                        <h3>Сохраненные тесты</h3>
                        <button
                            onClick={loadSavedTests}
                            className="btn btn-secondary"
                            title="Обновить список тестов"
                            aria-label="Обновить список тестов"
                        >
                            🔄 Обновить
                        </button>
                    </div>

                    {savedTests.length === 0 ? (
                        <div className="empty-tests">
                            <p>Нет сохраненных тестов</p>
                        </div>
                    ) : (
                        <div className="tests-list">
                            {savedTests.map(test => (
                                <div key={test.id} className="test-item">
                                    <div className="test-info">
                                        <h4>{test.filename}</h4>
                                        <p className="test-meta">
                                            ID: {test.id} |
                                            Документ: {getDocumentName(test.document_id)} |
                                            Создан: {formatDate(test.upload_timestamp)}
                                        </p>
                                    </div>
                                    <div className="test-actions">
                                        <button
                                            onClick={() => downloadTest(test.content, test.filename)}
                                            className="btn btn-secondary btn-sm"
                                            title="Скачать тест"
                                            aria-label={`Скачать тест ${test.filename}`}
                                        >
                                            📥 Скачать
                                        </button>
                                        <button
                                            onClick={() => deleteTest(test.id, test.filename)}
                                            className="btn btn-danger btn-sm"
                                            title="Удалить тест"
                                            aria-label={`Удалить тест ${test.filename}`}
                                        >
                                            🗑️ Удалить
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default TestGenerator;