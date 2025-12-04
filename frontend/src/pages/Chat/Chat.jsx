import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../../services/api';
import './Chat.css';

const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState('');
    const [selectedModel, setSelectedModel] = useState('lakomoor/vikhr-llama-3.2-1b-instruct:1b');
    const messagesEndRef = useRef(null);

    const models = [
        { value: 'lakomoor/vikhr-llama-3.2-1b-instruct:1b', label: '🦙 Llama 3.2' }
    ];

    // Генерируем session_id при монтировании
    useEffect(() => {
        const newSessionId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setSessionId(newSessionId);
    }, []);

    // Скролл к последнему сообщению
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();

        if (!inputMessage.trim()) return;

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: inputMessage,
            timestamp: new Date()
        };

        // Добавляем сообщение пользователя в историю
        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            // Отправляем сообщение на сервер
            const response = await chatAPI.sendMessage({
                question: inputMessage,
                session_id: sessionId,
                model: selectedModel
            });

            // Добавляем ответ ассистента в историю
            const assistantMessage = {
                id: Date.now() + 1,
                role: 'assistant',
                content: response.answer,
                timestamp: new Date(),
                model: response.model
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Error sending message:', error);

            // Добавляем сообщение об ошибке
            const errorMessage = {
                id: Date.now() + 1,
                role: 'error',
                content: `Ошибка: ${error.message}`,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    const clearChat = () => {
        setMessages([]);
        const newSessionId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setSessionId(newSessionId);
    };

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h2>💬 Чат с AI</h2>
                <div className="chat-controls">
                    <select
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        className="model-select"
                    >
                        {models.map(model => (
                            <option key={model.value} value={model.value}>
                                {model.label}
                            </option>
                        ))}
                    </select>
                    <button onClick={clearChat} className="btn-clear">
                        🗑️ Очистить чат
                    </button>
                </div>
            </div>

            <div className="chat-messages">
                {messages.length === 0 ? (
                    <div className="empty-chat">
                        <div className="welcome-message">
                            <h3>Добро пожаловать в чат!</h3>
                            <p>Задайте вопрос AI-ассистенту и получите ответ на основе ваших документов.</p>
                            <div className="examples">
                                <strong>Примеры вопросов:</strong>
                                <ul>
                                    <li>Объясни основные концепции из документа</li>
                                    <li>Создай вопросы для тестирования по этой теме</li>
                                    <li>Кратко суммируй ключевые моменты</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                ) : (
                    messages.map(message => (
                        <div key={message.id} className={`message ${message.role}`}>
                            <div className="message-content">
                                <div className="message-header">
                                    <span className="message-role">
                                        {message.role === 'user' ? '👤 Вы' :
                                            message.role === 'assistant' ? '🤖 AI' : '❌ Ошибка'}
                                    </span>
                                    <span className="message-time">
                                        {formatTime(message.timestamp)}
                                    </span>
                                </div>
                                <div className="message-text">
                                    {message.content}
                                </div>
                                {message.model && (
                                    <div className="message-model">
                                        Модель: {models.find(m => m.value === message.model)?.label || message.model}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="message assistant">
                        <div className="message-content">
                            <div className="message-header">
                                <span className="message-role">🤖 AI</span>
                            </div>
                            <div className="message-text loading">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSendMessage} className="chat-input-form">
                <div className="input-container">
                    <textarea
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Введите ваш вопрос..."
                        className="message-input"
                        rows="3"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="send-button"
                        disabled={!inputMessage.trim() || isLoading}
                    >
                        {isLoading ? '🔄' : '📤'}
                    </button>
                </div>
                <div className="input-hint">
                    Нажмите Enter для отправки, Shift+Enter для новой строки
                </div>
            </form>

            <div className="chat-info">
                <small>Session ID: {sessionId}</small>
            </div>
        </div>
    );
};

export default Chat;