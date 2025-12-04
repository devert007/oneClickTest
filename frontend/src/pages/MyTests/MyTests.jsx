import React, { useState, useEffect } from 'react';
import { testPDFAPI } from '../../services/api';
import './MyTests.css';

const MyTests = () => {
    const [tests, setTests] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedTest, setSelectedTest] = useState(null);
    const [connectionError, setConnectionError] = useState(false);

    // Функция проверки подключения к бэкенду
    const checkBackendConnection = async () => {
        try {
            const response = await fetch('http://localhost:8000/health');
            if (response.ok) {
                setConnectionError(false);
                return true;
            }
        } catch (error) {
            console.error('Backend connection failed:', error);
            setConnectionError(true);
            return false;
        }
        return false;
    };

    useEffect(() => {
        const initialize = async () => {
            const isConnected = await checkBackendConnection();
            if (isConnected) {
                loadTests();
            }
        };
        initialize();
    }, []);

    const loadTests = async () => {
        try {
            setIsLoading(true);
            const testList = await testPDFAPI.getTestPDFs();
            console.log('Loaded tests:', testList); // Для отладки
            setTests(testList);
        } catch (error) {
            console.error('Error loading tests:', error);
            setConnectionError(true);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (testId, filename) => {
        if (!window.confirm(`Удалить тест "${filename}"?`)) return;

        try {
            await testPDFAPI.deleteTestPDF(testId);
            await loadTests();
            if (selectedTest && selectedTest.id === testId) {
                setSelectedTest(null);
            }
        } catch (error) {
            console.error('Error deleting test:', error);
            alert(`Ошибка при удалении теста: ${error.message}`);
        }
    };

    const handleDownload = async (testId, filename) => {
        try {
            const pdfBlob = await testPDFAPI.downloadTestPDF(testId);
            const url = URL.createObjectURL(pdfBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading test:', error);
            alert(`Ошибка при скачивании теста: ${error.message}`);
        }
    };

    const handleViewTest = (test) => {
        setSelectedTest(test);
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('ru-RU');
    };

    return (
        <div className="my-tests">
            {connectionError && (
                <div className="connection-error">
                    <h3>⚠️ Нет подключения к серверу</h3>
                    <p>Убедитесь, что бэкенд запущен на http://localhost:8000</p>
                    <button onClick={checkBackendConnection} className="btn btn-warning">
                        Проверить подключение
                    </button>
                </div>
            )}

            <div className="page-header">
                <h1>Мои тесты</h1>
                <p>Просматривайте и управляйте созданными тестами</p>
            </div>

            <div className="tests-container">
                <div className="tests-list">
                    <div className="list-header">
                        <h3>Созданные тесты ({tests.length})</h3>
                        <button onClick={loadTests} className="btn btn-secondary" disabled={isLoading}>
                            {isLoading ? '🔄' : '🔃'} Обновить
                        </button>
                    </div>

                    {isLoading && tests.length === 0 ? (
                        <div className="loading">Загрузка тестов...</div>
                    ) : tests.length === 0 ? (
                        <div className="empty-state">
                            <p>📊 У вас пока нет созданных тестов</p>
                                <p>Перейдите в раздел {"Создать тест"} чтобы сгенерировать первый тест</p>
                        </div>
                    ) : (
                        <div className="tests-grid">
                            {tests.map(test => (
                                <div
                                    key={test.id}
                                    className={`test-card ${selectedTest?.id === test.id ? 'selected' : ''}`}
                                    onClick={() => handleViewTest(test)}
                                >
                                    <div className="test-info">
                                        <h4>{test.filename}</h4>
                                        <div className="test-meta">
                                            <span>ID: {test.id}</span>
                                            <span>Создан: {formatDate(test.upload_timestamp)}</span>
                                            {test.document_id && (
                                                <span>Документ ID: {test.document_id}</span>
                                            )}
                                            {test.session_id && (
                                                <span>Сессия: {test.session_id.substring(0, 8)}...</span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="test-actions">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDownload(test.id, test.filename);
                                            }}
                                            className="btn btn-secondary btn-sm"
                                        >
                                            📥 Скачать
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDelete(test.id, test.filename);
                                            }}
                                            className="btn btn-danger btn-sm"
                                        >
                                            🗑️ Удалить
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {selectedTest && (
                    <div className="test-preview">
                        <div className="preview-header">
                            <h3>Просмотр теста</h3>
                            <button
                                onClick={() => setSelectedTest(null)}
                                className="btn btn-secondary btn-sm"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="preview-content">
                            <h4>{selectedTest.filename}</h4>
                            <div className="test-details">
                                <p><strong>ID:</strong> {selectedTest.id}</p>
                                <p><strong>Создан:</strong> {formatDate(selectedTest.upload_timestamp)}</p>
                                {selectedTest.document_id && (
                                    <p><strong>Документ ID:</strong> {selectedTest.document_id}</p>
                                )}
                                {selectedTest.session_id && (
                                    <p><strong>Сессия:</strong> {selectedTest.session_id}</p>
                                )}
                            </div>
                            <div className="preview-actions">
                                <button
                                    onClick={() => handleDownload(selectedTest.id, selectedTest.filename)}
                                    className="btn btn-primary"
                                >
                                    📥 Скачать тест
                                </button>
                                <button
                                    onClick={() => handleDelete(selectedTest.id, selectedTest.filename)}
                                    className="btn btn-danger"
                                >
                                    🗑️ Удалить тест
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MyTests;