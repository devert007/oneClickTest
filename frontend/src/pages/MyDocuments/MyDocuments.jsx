import React, { useState, useEffect } from 'react';
import { documentAPI } from '../../services/api';
import './MyDocuments.css';

const MyDocuments = () => {
    const [documents, setDocuments] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
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
                loadDocuments();
            }
        };
        initialize();
    }, []);

    const loadDocuments = async () => {
        try {
            setIsLoading(true);
            const docs = await documentAPI.getDocuments();
            console.log('Loaded documents:', docs); // Для отладки
            setDocuments(docs);
        } catch (error) {
            console.error('Error loading documents:', error);
            setUploadStatus(`Ошибка: ${error.message}`);
            setConnectionError(true);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDownloadDocument = async (fileId, filename) => {
        try {
            await documentAPI.downloadDocument(fileId, filename);
            // Можно добавить небольшое уведомление об успешном скачивании
            setUploadStatus(`Документ "${filename}" успешно скачан`);
        } catch (error) {
            console.error('Error downloading document:', error);

            // Более информативное сообщение об ошибке
            if (error.message.includes('не найден')) {
                setUploadStatus(`Ошибка: Документ не найден в базе данных`);
            } else if (error.message.includes('недоступен')) {
                setUploadStatus(`Ошибка: Текст документа недоступен. Попробуйте загрузить документ заново.`);
            } else {
                setUploadStatus(`Ошибка при скачивании документа: ${error.message}`);
            }
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            setUploadStatus('');
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setUploadStatus('Пожалуйста, выберите файл');
            return;
        }

        setIsUploading(true);
        setUploadStatus('Загрузка...');

        try {
            // Сначала проверяем уникальность
            const uniquenessCheck = await documentAPI.checkUniqueness(selectedFile);

            if (!uniquenessCheck.is_unique) {
                setUploadStatus(`Документ не уникален: ${uniquenessCheck.message || uniquenessCheck.detail}`);
                return;
            }

            // Загружаем документ
            const result = await documentAPI.uploadDocument(selectedFile);
            setUploadStatus(`Документ "${selectedFile.name}" успешно загружен! ID: ${result.file_id}`);
            setSelectedFile(null);

            // Очищаем input файла
            const fileInput = document.getElementById('file-input');
            if (fileInput) fileInput.value = '';

            // Обновляем список документов
            await loadDocuments();
        } catch (error) {
            console.error('Error uploading document:', error);
            setUploadStatus(`Ошибка при загрузке документа: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsUploading(false);
        }
    };

    const handleDelete = async (fileId, filename) => {
        if (!window.confirm(`Вы уверены, что хотите удалить документ "${filename}"?`)) {
            return;
        }

        try {
            await documentAPI.deleteDocument(fileId);
            setUploadStatus(`Документ "${filename}" успешно удален`);
            await loadDocuments();
        } catch (error) {
            console.error('Error deleting document:', error);
            setUploadStatus(`Ошибка при удалении документа: ${error.response?.data?.detail || error.message}`);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('ru-RU');
    };

    return (
        <div className="my-documents">
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
                <h1>Мои документы</h1>
                <p>Управляйте вашими учебными материалами</p>
            </div>

            <div className="upload-section">
                <h3>Загрузить новый документ</h3>
                <div className="upload-area">
                    <input
                        id="file-input"
                        type="file"
                        accept=".pdf,.docx,.html,.txt"
                        onChange={handleFileSelect}
                        className="file-input"
                    />
                    <div className="upload-info">
                        {selectedFile && (
                            <div className="selected-file">
                                <strong>Выбран файл:</strong> {selectedFile.name}
                                <br />
                                <small>Размер: {Math.round(selectedFile.size / 1024)} KB</small>
                            </div>
                        )}
                    </div>
                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || isUploading}
                        className="btn btn-primary"
                    >
                        {isUploading ? '🔄 Загрузка...' : '📤 Загрузить документ'}
                    </button>
                </div>

                {uploadStatus && (
                    <div className={`status-message ${uploadStatus.includes('Ошибка') ? 'error' : 'success'}`}>
                        {uploadStatus}
                    </div>
                )}
            </div>

            <div className="documents-list">
                <div className="list-header">
                    <h3>Загруженные документы ({documents.length})</h3>
                    <button onClick={loadDocuments} className="btn btn-secondary" disabled={isLoading}>
                        {isLoading ? '🔄' : '🔃'} Обновить
                    </button>
                </div>

                {isLoading && documents.length === 0 ? (
                    <div className="loading">Загрузка документов...</div>
                ) : documents.length === 0 ? (
                    <div className="empty-state">
                        <p>📭 У вас пока нет загруженных документов</p>
                        <p>Загрузите первый документ чтобы начать создавать тесты</p>
                    </div>
                ) : (
                    <div className="documents-grid">
                        {documents.map(doc => (
                            <div key={doc.id} className="document-card">
                                <div className="document-info">
                                    <h4>{doc.filename}</h4>
                                    <div className="document-meta">
                                        <span>ID: {doc.id}</span>
                                        <span>Загружен: {formatDate(doc.upload_timestamp)}</span>
                                    </div>
                                </div>
                                <div className="document-actions">
                                    {/* ДОБАВЛЕНА КНОПКА СКАЧИВАНИЯ */}
                                    <button
                                        onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                                        className="btn btn-secondary"
                                        title="Скачать текст документа"
                                    >
                                        📥 Скачать текст
                                    </button>
                                    <button
                                        onClick={() => handleDelete(doc.id, doc.filename)}
                                        className="btn btn-danger"
                                        title="Удалить документ"
                                    >
                                        🗑️ Удалить
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="supported-formats">
                <h4>Поддерживаемые форматы:</h4>
                <ul>
                    <li>📄 PDF документы</li>
                    <li>📝 DOCX документы (Word)</li>
                </ul>
            </div>
        </div>
    );
};

export default MyDocuments;