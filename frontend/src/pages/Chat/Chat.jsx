import React, { useState, useEffect, useRef } from "react";
import { chatAPI } from "../../services/api";
import { Send, Trash2, Bot, UserIcon, AlertCircle, Sparkles } from "lucide-react";
import "./Chat.css";

const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState("");
    const messagesEndRef = useRef(null);

    useEffect(() => {
        const newSessionId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setSessionId(newSessionId);
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim()) return;

        const userMessage = {
            id: Date.now(),
            role: "user",
            content: inputMessage,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInputMessage("");
        setIsLoading(true);

        try {
            const response = await chatAPI.sendMessage({
                question: inputMessage,
                session_id: sessionId,
                model: "openai/gpt-oss-120b",
            });

            const assistantMessage = {
                id: Date.now() + 1,
                role: "assistant",
                content: response.answer,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error("Error sending message:", error);
            const errorMessage = {
                id: Date.now() + 1,
                role: "error",
                content: `Ошибка: ${error.message}`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
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
        return new Date(timestamp).toLocaleTimeString("ru-RU", {
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    return (
        <div className="chat-container">
            <div className="chat-toolbar">
                <button onClick={clearChat} className="chat-clear-btn">
                    <Trash2 size={16} />
                    <span>Очистить</span>
                </button>
            </div>

            <div className="chat-messages">
                {messages.length === 0 ? (
                    <div className="chat-empty">
                        <div className="chat-empty-icon">
                            <Sparkles size={40} />
                        </div>
                        <h3>Начните диалог</h3>
                        <p>Задайте вопрос AI-ассистенту по вашим документам</p>
                        <div className="chat-suggestions">
                            {[
                                "Объясни основные концепции из документа",
                                "Кратко суммируй ключевые моменты",
                                "Какие темы затрагивает документ?"
                            ].map((s, i) => (
                                <button
                                    key={i}
                                    className="chat-suggestion"
                                    onClick={() => setInputMessage(s)}
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    messages.map((message) => (
                        <div key={message.id} className={`chat-msg chat-msg--${message.role}`}>
                            <div className="chat-msg-avatar">
                                {message.role === "user" ? (
                                    <UserIcon size={18} />
                                ) : message.role === "assistant" ? (
                                    <Bot size={18} />
                                ) : (
                                    <AlertCircle size={18} />
                                )}
                            </div>
                            <div className="chat-msg-body">
                                <div className="chat-msg-meta">
                                    <span className="chat-msg-sender">
                                        {message.role === "user" ? "Вы" : message.role === "assistant" ? "AI" : "Ошибка"}
                                    </span>
                                    <span className="chat-msg-time">{formatTime(message.timestamp)}</span>
                                </div>
                                <div className="chat-msg-text">{message.content}</div>
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="chat-msg chat-msg--assistant">
                        <div className="chat-msg-avatar">
                            <Bot size={18} />
                        </div>
                        <div className="chat-msg-body">
                            <div className="chat-msg-meta">
                                <span className="chat-msg-sender">AI</span>
                            </div>
                            <div className="chat-msg-text">
                                <div className="typing-dots">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSendMessage} className="chat-input-area">
                <div className="chat-input-wrap">
                    <textarea
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Напишите сообщение..."
                        className="chat-textarea"
                        rows="1"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="chat-send-btn"
                        disabled={!inputMessage.trim() || isLoading}
                    >
                        <Send size={18} />
                    </button>
                </div>
                <p className="chat-hint">Enter — отправить, Shift+Enter — новая строка</p>
            </form>
        </div>
    );
};

export default Chat;
