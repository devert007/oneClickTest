import React, { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../../services/api';
import './ChatInterface.css';

const ChatInterface = ({ sessionId, onSessionIdChange, model, onModelChange }) => {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim() || isLoading) return;

        const userMessage = {
            role: 'user',
            content: inputMessage,
            timestamp: new Date().toLocaleTimeString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            const response = await chatAPI.sendMessage(inputMessage, sessionId, model);

            const aiMessage = {
                role: 'assistant',
                content: response.answer,
                sessionId: response.session_id,
                model: response.model,
                timestamp: new Date().toLocaleTimeString()
            };

            setMessages(prev => [...prev, aiMessage]);

            if (!sessionId && response.session_id) {
                onSessionIdChange(response.session_id);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage = {
                role: 'error',
                content: 'Ошибка при получении ответа. Попробуйте еще раз.',
                timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        setMessages([]);
    };

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <h3>Чат с AI</h3>
                <div className="chat-controls">
                    <div className="model-selector">
                        <label>Модель:</label>
                        <select
                            value={model}
                            onChange={(e) => onModelChange(e.target.value)}
                        >
                            <option value="llama3.2">Llama 3.2</option>
                            <option value="gpt-4o">GPT-4o</option>
                            <option value="gpt-4o-mini">GPT-4o Mini</option>
                        </select>
                    </div>
                    <button
                        className="btn btn-secondary"
                        onClick={clearChat}
                        disabled={messages.length === 0}
                    >
                        Очистить чат
                    </button>
                </div>
            </div>

            <div className="messages-container">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <p>Задайте вопрос AI для генерации тестовых вопросов</p>
                    </div>
                ) : (
                    messages.map((message, index) => (
                        <div key={index} className={`message ${message.role}`}>
                            <div className="message-content">
                                <div className="message-header">
                                    <span className="message-role">
                                        {message.role === 'user' ? '👤 Вы' :
                                            message.role === 'assistant' ? '🤖 AI' : '❌ Ошибка'}
                                    </span>
                                    <span className="message-time">{message.timestamp}</span>
                                </div>
                                <div className="message-text">{message.content}</div>
                                {message.role === 'assistant' && (
                                    <div className="message-meta">
                                        <span>Модель: {message.model}</span>
                                        {message.sessionId && (
                                            <span>Сессия: {message.sessionId.slice(0, 8)}...</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="message assistant">
                        <div className="message-content">
                            <div className="loading-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSendMessage} className="chat-input-form">
                <div className="input-group">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Введите ваш вопрос..."
                        disabled={isLoading}
                        className="chat-input"
                    />
                    <button
                        type="submit"
                        disabled={!inputMessage.trim() || isLoading}
                        className="btn btn-primary send-button"
                    >
                        {isLoading ? '⏳' : '📤'}
                    </button>
                </div>
            </form>

            {sessionId && (
                <div className="session-info">
                    <small>Session ID: {sessionId}</small>
                </div>
            )}
        </div>
    );
};

export default ChatInterface;