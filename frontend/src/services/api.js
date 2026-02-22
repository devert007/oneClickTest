import axios from 'axios';
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

// Обработчик ошибок
const handleApiError = (error, defaultMessage = 'Произошла ошибка') => {
    if (error.response) {
        return error.response.data?.detail || error.response.data?.message || defaultMessage;
    } else if (error.request) {
        return 'Сервер не отвечает. Проверьте, запущен ли бэкенд.';
    } else {
        return error.message || defaultMessage;
    }
};

api.interceptors.response.use(
    response => response,
    error => {
        const message = handleApiError(error);
        throw new Error(message);
    }
);

// Сервис для документов
export const documentAPI = {
    getDocuments: async () => {
        const response = await api.get('/list-docs');
        return response.data;
    },

    uploadDocument: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post('/upload-doc', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 30000,
        });
        return response.data;
    },

    deleteDocument: async (fileId) => {
        const response = await api.post('/delete-doc', { file_id: fileId });
        return response.data;
    },

    checkUniqueness: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post('/check-uniqueness', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getDocumentText: async (fileId) => {
        const response = await api.get(`/get-document-text/${fileId}`);
        return response.data;
    },

    downloadDocument: async (fileId, filename) => {
        try {
            // Используем существующий эндпоинт /get-document-text
            const response = await api.get(`/get-document-text/${fileId}`);

            // Получаем текст из ответа
            const documentText = response.data.text;

            // Создаем blob и ссылку для скачивания
            const blob = new Blob([documentText], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Создаем имя файла
            const downloadFilename = filename ?
                `${filename.replace(/\.[^/.]+$/, "")}_text.txt` :
                `document_${fileId}.txt`;

            a.download = downloadFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            console.log(`Документ ${downloadFilename} успешно скачан`);
            return { success: true, filename: downloadFilename };
        } catch (error) {
            console.error('Error downloading document:', error);

            // Более информативное сообщение об ошибке
            let errorMessage = 'Ошибка при скачивании документа';
            if (error.response?.status === 404) {
                errorMessage = 'Документ не найден в базе данных';
            } else if (error.response?.status === 500) {
                errorMessage = 'Текст документа недоступен. Возможно, документ был загружен до реализации системы индексации.';
            }

            throw new Error(errorMessage);
        }
    }
};

// Сервис для тестовых PDF
export const testPDFAPI = {
    getTestPDFs: async () => {
        const response = await api.get('/list-test-pdfs');
        return response.data;
    },

    uploadTestPDF: async (file, documentId = null, sessionId = null) => {
        const formData = new FormData();
        formData.append('file', file);
        if (documentId) formData.append('document_id', documentId);
        if (sessionId) formData.append('session_id', sessionId);

        const response = await api.post('/upload-test-pdf', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    downloadTestPDF: async (fileId) => {
        const response = await api.get(`/download-test-pdf/${fileId}`, {
            responseType: 'blob'
        });
        return response.data;
    },

    deleteTestPDF: async (fileId) => {
        const response = await api.post('/delete-test-pdf', { file_id: fileId });
        return response.data;
    }
};

// Сервис для генерации тестов
export const testGenerationAPI = {
    generateTest: async (testData) => {
        const response = await api.post('/generate-test', testData, {
            timeout: 300000,
        });
        return response.data;
    },

    // Сохранение теста через новый эндпоинт
    saveTest: async (testContent, filename, documentId = null, sessionId = null) => {
        try {
            console.log('💾 Сохранение теста через /save-test:', { 
                filename, 
                documentId, 
                contentLength: testContent.length 
            });
            
            const formData = new FormData();
            formData.append('test_content', testContent);
            formData.append('filename', filename);
            if (documentId) formData.append('document_id', documentId);
            if (sessionId) formData.append('session_id', sessionId);

            const response = await api.post('/save-test', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 60000,
            });
            
            console.log('✅ Тест сохранен через /save-test:', response.data);
            return response.data;
            
        } catch (error) {
            console.error('❌ Ошибка при сохранении через /save-test:', error);
            
            // Если новый метод не работает, пробуем старый через uploadTestPDF
            console.log('🔄 Пробуем альтернативный метод сохранения...');
            return await testGenerationAPI.saveTestOld(testContent, filename, documentId, sessionId);
        }
    },

    // Старый метод для обратной совместимости
    saveTestOld: async (testContent, filename, documentId = null, sessionId = null) => {
        try {
            console.log('📤 Используем старый метод сохранения через uploadTestPDF');
            
            // Создаем Markdown файл
            const blob = new Blob([testContent], { type: 'text/markdown' });
            const file = new File([blob], filename, { type: 'text/markdown' });

            // Используем существующий uploadTestPDF
            const result = await testPDFAPI.uploadTestPDF(file, documentId, sessionId);
            console.log('✅ Тест сохранен через старый метод:', result);
            return result;
        } catch (error) {
            console.error('❌ Ошибка в старом методе сохранения:', error);
            throw error;
        }
    }
};
export const chatAPI = {
    sendMessage: async (messageData) => {
        try {
            console.log('📤 Sending chat message:', messageData);
            const response = await api.post('/chat', messageData);
            console.log('📥 Chat response received:', response.data);
            return response.data;
        } catch (error) {
            console.error('API Error sending chat message:', error);

            // Более информативные сообщения об ошибках для чата
            let errorMessage = 'Ошибка при отправке сообщения';
            if (error.response?.status === 500) {
                errorMessage = 'Ошибка на сервере. Попробуйте позже.';
            } else if (error.message.includes('timeout')) {
                errorMessage = 'Превышено время ожидания ответа. Попробуйте еще раз.';
            } else if (error.message.includes('Network Error')) {
                errorMessage = 'Проблемы с подключением к серверу. Проверьте интернет-соединение.';
            }

            throw new Error(errorMessage);
        }
    }
};

export default api;