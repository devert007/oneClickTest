import React, { useState, useEffect } from 'react';
import { documentAPI } from '../../services/api';
import './DocumentManager.css';

const DocumentManager = () => {
    const [documents, setDocuments] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [documentPreview, setDocumentPreview] = useState(null);

    useEffect(() => {
        loadDocuments();
    }, []);

    const loadDocuments = async () => {
        try {
            setIsLoading(true);
            const docs = await documentAPI.getDocumentsWithContent();
            setDocuments(docs);
        } catch (error) {
            console.error('Error loading documents:', error);
            setUploadStatus('Ошибка при загрузке списка документов');
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            setUploadStatus('');
            setDocumentPreview(null);

            if (file.type === 'text/plain' || file.name.endsWith('.html')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    setDocumentPreview(e.target.result.slice(0, 500) + '...');
                };
                reader.readAsText(file);
            }
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setUploadStatus('Пожалуйста, выберите файл');
            return;
        }

        setIsLoading(true);
        setUploadStatus('Загрузка...');

        try {
            const uniquenessCheck = await documentAPI.checkUniqueness(selectedFile);

            if (!uniquenessCheck.is_unique) {
                setUploadStatus(`Документ не уникален: ${uniquenessCheck.message}`);
                return;
            }

            const result = await documentAPI.uploadDocument(selectedFile);
            setUploadStatus(`Документ "${selectedFile.name}" успешно загружен! ID: ${result.file_id}`);
            setSelectedFile(null);
            setDocumentPreview(null);

            const fileInput = document.getElementById('file-input');
            if (fileInput) fileInput.value = '';

            await loadDocuments();
        } catch (error) {
            console.error('Error uploading document:', error);
            setUploadStatus(`Ошибка при загрузке документа: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsLoading(false);
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
            setUploadStatus('Ошибка при удалении документа');
        }
    };

    const handleDownloadText = async (fileId, filename) => {
        try {
            const result = await documentAPI.getDocumentText(fileId);

            const blob = new Blob([result.text], { type: 'text/plain; charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}_text.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading text:', error);
            setUploadStatus('Ошибка при скачивании текста');
        }
    };

    const handleViewContent = async (fileId, filename) => {
        try {
            const result = await documentAPI.getDocumentText(fileId);
            // Показываем содержимое в модальном окне
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            `;

            const content = document.createElement('div');
            content.style.cssText = `
                background: white;
                padding: 20px;
                border-radius: 10px;
                max-width: 80%;
                max-height: 80%;
                overflow: auto;
                position: relative;
            `;

            const closeBtn = document.createElement('button');
            closeBtn.textContent = '✕';
            closeBtn.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                cursor: pointer;
            `;
            closeBtn.onclick = () => document.body.removeChild(modal);

            const title = document.createElement('h3');
            title.textContent = `Содержимое документа: ${filename}`;

            const text = document.createElement('pre');
            text.textContent = result.text;
            text.style.cssText = `
                white-space: pre-wrap;
                word-wrap: break-word;
                margin-top: 15px;
                font-family: inherit;
            `;

            content.appendChild(closeBtn);
            content.appendChild(title);
            content.appendChild(text);
            modal.appendChild(content);
            document.body.appendChild(modal);

            // Закрытие по клику вне контента
            modal.onclick = (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                }
            };
        } catch (error) {
            console.error('Error viewing content:', error);
            setUploadStatus('Ошибка при загрузке содержимого документа');
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('ru-RU');
    };

    const formatFileSize = (content) => {
        if (!content) return '0 KB';
        const sizeInKB = Math.ceil(content.length / 1024);
        return sizeInKB < 1024 ? `${sizeInKB} KB` : `${(sizeInKB / 1024).toFixed(1)} MB`;
    };

    const getPreview = (doc) => {
        if (doc.preview) return doc.preview;
        if (doc.content) return doc.content.slice(0, 200) + '...';
        return 'Содержимое не доступно';
    };

    return (
        <div className="document-manager">
            <h2>Управление документами</h2>

            {/* Секция загрузки */}
            <div className="upload-section card">
                <h3>Загрузить новый документ</h3>
                <div className="upload-form">
                    <input
                        id="file-input"
                        type="file"
                        accept=".pdf,.docx,.html,.txt"
                        onChange={handleFileSelect}
                        className="file-input"
                    />
                    <div className="file-info">
                        {selectedFile && (
                            <div className="selected-file">
                                <strong>Выбран файл:</strong> {selectedFile.name}
                                <br />
                                <strong>Размер:</strong> {Math.round(selectedFile.size / 1024)} KB
                                <br />
                                <strong>Тип:</strong> {selectedFile.type || 'Неизвестно'}
                                {documentPreview && (
                                    <>
                                        <br />
                                        <strong>Превью:</strong>
                                        <div className="file-preview">
                                            {documentPreview}
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || isLoading}
                        className="btn btn-primary upload-btn"
                    >
                        {isLoading ? '🔄 Загрузка...' : '📤 Загрузить документ'}
                    </button>
                </div>
                {uploadStatus && (
                    <div className={`status-message ${uploadStatus.includes('Ошибка') ? 'error' : 'success'}`}>
                        {uploadStatus}
                    </div>
                )}
            </div>

            {/* Список документов */}
            <div className="documents-list card">
                <div className="documents-header">
                    <h3>Загруженные документы</h3>
                    <div className="header-actions">
                        <span className="documents-count">
                            Всего: {documents.length} документов
                        </span>
                        <button
                            onClick={loadDocuments}
                            className="btn btn-secondary"
                            disabled={isLoading}
                        >
                            {isLoading ? '🔄' : '🔃'} Обновить
                        </button>
                    </div>
                </div>

                {isLoading && documents.length === 0 ? (
                    <div className="loading-documents">
                        <div className="loading-spinner"></div>
                        <p>Загрузка документов...</p>
                    </div>
                ) : documents.length === 0 ? (
                    <div className="empty-documents">
                        <p>📭 Нет загруженных документов</p>
                        <p>Загрузите первый документ чтобы начать работу</p>
                    </div>
                ) : (
                    <div className="documents-grid">
                        {documents.map((doc) => (
                            <div key={doc.id} className="document-card">
                                <div className="document-header">
                                    <h4 className="document-name">
                                        {doc.filename}
                                        {doc.content && <span className="content-indicator">📄</span>}
                                    </h4>
                                    <span className="document-id">ID: {doc.id}</span>
                                </div>

                                <div className="document-meta">
                                    <span className="upload-date">
                                        📅 {formatDate(doc.upload_timestamp)}
                                    </span>
                                    <span className="file-size">
                                        💾 {formatFileSize(doc.content)}
                                    </span>
                                </div>

                                <div className="document-preview">
                                    <strong>Превью:</strong>
                                    <p className="preview-text">{getPreview(doc)}</p>
                                </div>

                                <div className="document-actions">
                                    <button
                                        onClick={() => handleViewContent(doc.id, doc.filename)}
                                        className="btn btn-info btn-sm"
                                        title="Просмотреть содержимое"
                                        disabled={!doc.content}
                                    >
                                        👁️ Просмотр
                                    </button>
                                    <button
                                        onClick={() => handleDownloadText(doc.id, doc.filename)}
                                        className="btn btn-secondary btn-sm"
                                        title="Скачать текст"
                                        disabled={!doc.content}
                                    >
                                        📥 Текст
                                    </button>
                                    <button
                                        onClick={() => handleDelete(doc.id, doc.filename)}
                                        className="btn btn-danger btn-sm"
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

            {/* Информация о поддерживаемых форматах */}
            <div className="info-section card">
                <h4>📋 Поддерживаемые форматы:</h4>
                <ul className="formats-list">
                    <li>📄 PDF документы</li>
                    <li>📝 DOCX документы (Word)</li>
                </ul>
                <div className="system-info">
                    <p className="info-note">
                        💡 Документы индексируются в векторную базу ChromaDB для семантического поиска
                    </p>
                    <p className="info-note">
                        🔍 После загрузки документы автоматически разбиваются на фрагменты и добавляются в базу знаний
                    </p>
                </div>
            </div>

            {/* Статистика */}
            {documents.length > 0 && (
                <div className="stats-section card">
                    <h4>📊 Статистика</h4>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <span className="stat-number">{documents.length}</span>
                            <span className="stat-label">Всего документов</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-number">
                                {documents.filter(d => d.content).length}
                            </span>
                            <span className="stat-label">Доступно содержимое</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-number">
                                {formatFileSize(documents.map(d => d.content).join(''))}
                            </span>
                            <span className="stat-label">Общий размер</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DocumentManager;