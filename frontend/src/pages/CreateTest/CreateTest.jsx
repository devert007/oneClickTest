import React, { useState, useEffect } from "react";
import { documentAPI, testGenerationAPI, testPDFAPI } from "../../services/api";
import { googleFormAPI } from "../../services/googleFormAPI";
import {
    Zap, Save, Download, FileDown, FilePlus, Trash2,
    RefreshCw, Upload, X, CheckCircle, AlertTriangle,
    ClipboardCheck, Archive, ExternalLink, Loader2,
    Mic, MicOff, Sparkles
} from "lucide-react";
import useSpeechRecognition from "../../hooks/useSpeechRecognition";
import "./CreateTest.css";

const CreateTest = () => {
    const [documents, setDocuments] = useState([]);
    const [googleFormStatus, setGoogleFormStatus] = useState("");

    const handleSendToGoogleForm = async () => {
        if (!generatedTest || (!generatedTest.test_json && !generatedTest.test_content)) {
            alert("Нет сгенерированного теста для отправки");
            return;
        }
        setGoogleFormStatus("Отправка...");
        try {
            const testJson = generatedTest.test_json || JSON.parse(generatedTest.test_content);
            const result = await googleFormAPI.sendTestToGoogleForm(testJson);
            const scriptResp = result.script_response || result;

            if (scriptResp.success && scriptResp.formUrl) {
                setGoogleFormStatus("success");
                setGeneratedTest((prev) => ({
                    ...prev,
                    googleFormUrl: scriptResp.formUrl,
                }));
            }
        } catch (error) {
            setGoogleFormStatus("error");
            alert("Ошибка при отправке в Google Apps Script: " + error.message);
        }
    };

    const [selectedDocument, setSelectedDocument] = useState("");
    const [testParams, setTestParams] = useState({
        questionCount: 10,
        difficulty: "Для средних классов",
        questionType: "multiple_choice",
        includeAnswers: true,
        model: "openai/gpt-oss-120b",
    });
    const [generatedTest, setGeneratedTest] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [savedTests, setSavedTests] = useState([]);
    const [activeTab, setActiveTab] = useState("generate");

    const [newDocumentFile, setNewDocumentFile] = useState(null);
    const [isUploadingDocument, setIsUploadingDocument] = useState(false);
    const [uploadDocumentStatus, setUploadDocumentStatus] = useState("");
    const [showUploadForm, setShowUploadForm] = useState(false);

    const [promptText, setPromptText] = useState("");
    const [speechLang, setSpeechLang] = useState("ru-RU");
    const [isGeneratingFromPrompt, setIsGeneratingFromPrompt] = useState(false);
    const [promptGenerationStatus, setPromptGenerationStatus] = useState("");

    const {
        isListening,
        error: speechError,
        interimTranscript,
        start: startListening,
        stop: stopListening,
        supported: speechSupported,
    } = useSpeechRecognition({
        lang: speechLang,
        onResult: (text) => {
            setPromptText((prev) => (prev ? `${prev} ${text}` : text));
        },
    });

    const toggleListening = () => {
        if (isListening) stopListening();
        else startListening();
    };

    const difficultyLevels = [
        { value: "Для начальных классов", label: "Для начальных классов" },
        { value: "Для средних классов", label: "Для средних классов" },
        { value: "Для старших классов", label: "Для старших классов" },
        { value: "Для студентов", label: "Для студентов" },
    ];

    const questionTypes = [
        { value: "multiple_choice", label: "Множественный выбор" },
        { value: "open_questions", label: "Открытые вопросы" },
    ];

    useEffect(() => {
        loadDocuments();
        loadSavedTests();
    }, []);

    const loadDocuments = async () => {
        try {
            const docs = await documentAPI.getDocuments();
            setDocuments(docs);
        } catch (error) {
            console.error("Error loading documents:", error);
        }
    };

    const loadSavedTests = async () => {
        try {
            const tests = await testPDFAPI.getTestPDFs();
            setSavedTests(tests);
        } catch (error) {
            console.error("Error loading saved tests:", error);
        }
    };

    const handleUploadNewDocument = async () => {
        if (!newDocumentFile) {
            setUploadDocumentStatus("Пожалуйста, выберите файл");
            return;
        }

        setIsUploadingDocument(true);
        setUploadDocumentStatus("Загрузка...");

        try {
            const uniquenessCheck = await documentAPI.checkUniqueness(newDocumentFile);
            if (!uniquenessCheck.is_unique) {
                setUploadDocumentStatus(
                    `Документ не уникален: ${uniquenessCheck.message || uniquenessCheck.detail}`
                );
                return;
            }

            const result = await documentAPI.uploadDocument(newDocumentFile);
            setUploadDocumentStatus(
                `Документ "${newDocumentFile.name}" успешно загружен!`
            );
            setNewDocumentFile(null);

            const fileInput = document.getElementById("new-document-file-input");
            if (fileInput) fileInput.value = "";

            await loadDocuments();
            setSelectedDocument(result.file_id.toString());
            setShowUploadForm(false);
        } catch (error) {
            console.error("Error uploading document:", error);
            setUploadDocumentStatus(
                `Ошибка: ${error.response?.data?.detail || error.message}`
            );
        } finally {
            setIsUploadingDocument(false);
        }
    };

    const handleNewDocumentFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setNewDocumentFile(file);
            setUploadDocumentStatus("");
        }
    };

    const generateTest = async () => {
        if (!selectedDocument) {
            alert("Пожалуйста, выберите документ для генерации теста");
            return;
        }

        setIsGenerating(true);
        setGeneratedTest(null);
        const generationTimeout = setTimeout(() => {
            alert("Генерация занимает больше времени, чем ожидалось. Пожалуйста, подождите...");
        }, 20000);

        try {
            const requestData = {
                question_count: testParams.questionCount,
                difficulty: testParams.difficulty,
                question_type: testParams.questionType,
                include_answers: testParams.includeAnswers,
                model: testParams.model,
                session_id: `session_${Date.now()}`,
            };

            if (selectedDocument) {
                requestData.document_id = parseInt(selectedDocument);
            }

            const result = await testGenerationAPI.generateTest(requestData);
            clearTimeout(generationTimeout);
            setGeneratedTest(result);
        } catch (error) {
            console.error("Error generating test:", error);
            alert(`Ошибка при генерации теста: ${error.message}`);
        } finally {
            clearTimeout(generationTimeout);
            setIsGenerating(false);
        }
    };

    const generateFromPrompt = async () => {
        const trimmed = promptText.trim();
        if (trimmed.length < 3) {
            setPromptGenerationStatus("Введите описание теста (например: «Тест для 8 класса по биологии»)");
            return;
        }

        setIsGeneratingFromPrompt(true);
        setPromptGenerationStatus("Генерирую учебный материал и тест... Это может занять до минуты.");
        setGeneratedTest(null);

        try {
            const payload = {
                prompt: trimmed,
                question_count: testParams.questionCount,
                difficulty: testParams.difficulty,
                question_type: testParams.questionType,
                include_answers: testParams.includeAnswers,
                model: testParams.model,
                session_id: `session_${Date.now()}`,
            };
            const result = await testGenerationAPI.generateMaterialAndTest(payload);

            setGeneratedTest(result);
            if (result.document_id) {
                setSelectedDocument(String(result.document_id));
            }
            await loadDocuments();
            setPromptGenerationStatus(
                `Материал сохранён как документ "${result.document_filename}". Тест готов.`
            );
            setActiveTab("generate");
        } catch (error) {
            console.error("Error generating from prompt:", error);
            setPromptGenerationStatus(`Ошибка: ${error.message}`);
        } finally {
            setIsGeneratingFromPrompt(false);
        }
    };

    const downloadTestFromBackend = async (fileId, filename = `test_${Date.now()}.pdf`) => {
        try {
            const blob = await testPDFAPI.downloadTestPDF(fileId);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            return { success: true, filename };
        } catch (error) {
            console.error("Error downloading test from backend:", error);
            alert(`Ошибка при скачивании теста: ${error.message}`);
            throw error;
        }
    };

    const saveTest = async () => {
        if (!generatedTest) return;

        try {
            const filename = `test_${Date.now()}.md`;
            const documentId = selectedDocument ? parseInt(selectedDocument) : null;
            const sessionId = generatedTest.session_id || `session_${Date.now()}`;

            setIsGenerating(true);

            const result = await testGenerationAPI.saveTest(
                generatedTest.test_content, filename, documentId, sessionId
            );

            setGeneratedTest((prev) => ({
                ...prev,
                savedFileId: result.file_id,
                savedFilename: result.filename || filename.replace(".md", ".pdf"),
            }));

            setIsGenerating(false);
            alert(`Тест успешно сохранен! ID: ${result.file_id}`);
            await loadSavedTests();
        } catch (error) {
            console.error("Error saving test:", error);
            setIsGenerating(false);
            alert(`Ошибка при сохранении: ${error.message}`);
        }
    };

    const handleDownloadFromBackend = async () => {
        if (!generatedTest?.savedFileId) {
            alert("Сначала сохраните тест, чтобы скачать PDF");
            return;
        }

        try {
            await downloadTestFromBackend(
                generatedTest.savedFileId,
                generatedTest.savedFilename.replace(".md", ".pdf")
            );
        } catch (error) {
            console.error("Error downloading from backend:", error);
        }
    };

    const handleSaveAndDownload = async () => {
        if (!generatedTest) return;

        try {
            const filename = `test_${Date.now()}.md`;
            const documentId = selectedDocument ? parseInt(selectedDocument) : null;
            const sessionId = generatedTest.session_id || `session_${Date.now()}`;

            setIsGenerating(true);

            const result = await testGenerationAPI.saveTest(
                generatedTest.test_content, filename, documentId, sessionId
            );

            await downloadTestFromBackend(result.file_id, result.filename);

            setIsGenerating(false);
            alert("Тест сохранен и скачан!");
            await loadSavedTests();
        } catch (error) {
            console.error("Error in save and download:", error);
            setIsGenerating(false);
            alert(`Ошибка: ${error.message}`);
        }
    };

    const downloadTest = (testContent, filename = `test_${Date.now()}.md`) => {
        const blob = new Blob([testContent], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
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
        } catch (error) {
            console.error("Error deleting test:", error);
            alert(`Ошибка при удалении теста: ${error.message}`);
        }
    };

    const formatDate = (dateString) => new Date(dateString).toLocaleString("ru-RU");

    const getDocumentName = (documentId) => {
        const doc = documents.find((d) => d.id === documentId);
        return doc ? doc.filename : "Не указан";
    };

    return (
        <div className="create-test">
            <div className="ct-tabs">
                <button
                    className={`ct-tab ${activeTab === "generate" ? "active" : ""}`}
                    onClick={() => setActiveTab("generate")}
                >
                    <ClipboardCheck size={18} />
                    <span>По документу</span>
                </button>
                <button
                    className={`ct-tab ${activeTab === "prompt" ? "active" : ""}`}
                    onClick={() => setActiveTab("prompt")}
                >
                    <Sparkles size={18} />
                    <span>По промпту</span>
                </button>
                <button
                    className={`ct-tab ${activeTab === "saved" ? "active" : ""}`}
                    onClick={() => setActiveTab("saved")}
                >
                    <Archive size={18} />
                    <span>Сохранённые ({savedTests.length})</span>
                </button>
            </div>

            {activeTab === "generate" && (
                <>
                    <div className="ct-panel">
                        <h3 className="ct-panel-title">Параметры теста</h3>

                        <div className="ct-grid">
                            <div className="ct-field">
                                <label htmlFor="document-select">Документ</label>
                                <select
                                    id="document-select"
                                    value={selectedDocument}
                                    onChange={(e) => setSelectedDocument(e.target.value)}
                                    className="form-control"
                                >
                                    <option value="">Выберите документ...</option>
                                    {documents.map((doc) => (
                                        <option key={doc.id} value={doc.id}>
                                            {doc.filename} (ID: {doc.id})
                                        </option>
                                    ))}
                                </select>

                                <button
                                    type="button"
                                    onClick={() => setShowUploadForm(!showUploadForm)}
                                    className="ct-upload-toggle"
                                >
                                    {showUploadForm ? <X size={14} /> : <Upload size={14} />}
                                    <span>{showUploadForm ? "Отменить" : "Загрузить новый"}</span>
                                </button>

                                {showUploadForm && (
                                    <div className="ct-upload-box">
                                        <input
                                            id="new-document-file-input"
                                            type="file"
                                            accept=".pdf,.docx,.html,.txt"
                                            onChange={handleNewDocumentFileSelect}
                                            className="form-control"
                                        />
                                        {newDocumentFile && (
                                            <div className="ct-file-info">
                                                <CheckCircle size={14} />
                                                <span>{newDocumentFile.name} ({Math.round(newDocumentFile.size / 1024)} KB)</span>
                                            </div>
                                        )}
                                        <div className="ct-upload-actions">
                                            <button
                                                onClick={handleUploadNewDocument}
                                                disabled={!newDocumentFile || isUploadingDocument}
                                                className="btn btn-primary btn-sm"
                                            >
                                                {isUploadingDocument ? <><Loader2 size={14} className="spin" /> Загрузка...</> : <><Upload size={14} /> Загрузить</>}
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => { setShowUploadForm(false); setNewDocumentFile(null); setUploadDocumentStatus(""); }}
                                                className="btn btn-secondary btn-sm"
                                            >
                                                Отмена
                                            </button>
                                        </div>
                                        {uploadDocumentStatus && (
                                            <div className={`ct-status ${uploadDocumentStatus.includes("Ошибка") ? "error" : "success"}`}>
                                                {uploadDocumentStatus}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            <div className="ct-field">
                                <label htmlFor="total-question-count">Количество вопросов</label>
                                <input
                                    id="total-question-count"
                                    type="number"
                                    min="1"
                                    max="50"
                                    value={testParams.questionCount}
                                    onChange={(e) =>
                                        setTestParams((prev) => ({ ...prev, questionCount: parseInt(e.target.value) }))
                                    }
                                    className="form-control"
                                    placeholder="1 — 50"
                                />
                            </div>

                            <div className="ct-field">
                                <label htmlFor="difficulty-select">Сложность</label>
                                <select
                                    id="difficulty-select"
                                    value={testParams.difficulty}
                                    onChange={(e) =>
                                        setTestParams((prev) => ({ ...prev, difficulty: e.target.value }))
                                    }
                                    className="form-control"
                                >
                                    {difficultyLevels.map((level) => (
                                        <option key={level.value} value={level.value}>{level.label}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="ct-field">
                                <label htmlFor="question-type-select">Тип вопросов</label>
                                <select
                                    id="question-type-select"
                                    value={testParams.questionType}
                                    onChange={(e) =>
                                        setTestParams((prev) => ({ ...prev, questionType: e.target.value }))
                                    }
                                    className="form-control"
                                >
                                    {questionTypes.map((type) => (
                                        <option key={type.value} value={type.value}>{type.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <label className="ct-checkbox">
                            <input
                                type="checkbox"
                                checked={testParams.includeAnswers}
                                onChange={(e) =>
                                    setTestParams((prev) => ({ ...prev, includeAnswers: e.target.checked }))
                                }
                            />
                            <span>Включать ответы</span>
                        </label>

                        <button
                            onClick={generateTest}
                            disabled={isGenerating || !selectedDocument}
                            className="btn btn-primary ct-generate-btn"
                        >
                            {isGenerating ? (
                                <><Loader2 size={18} className="spin" /> Генерация...</>
                            ) : (
                                <><Zap size={18} /> Сгенерировать тест</>
                            )}
                        </button>

                        {documents.length === 0 && (
                            <div className="ct-warning">
                                <AlertTriangle size={16} />
                                <span>Загрузите документ для генерации тестов</span>
                            </div>
                        )}
                    </div>

                    {generatedTest && (
                        <div className="ct-result">
                            <div className="ct-result-header">
                                <h3>Результат</h3>
                                <span className="ct-result-badge">{testParams.questionCount} вопросов</span>
                            </div>

                            <div className="ct-result-actions">
                                <button onClick={saveTest} className="btn btn-primary btn-sm">
                                    <Save size={15} /> Сохранить
                                </button>
                                <button onClick={() => downloadTest(generatedTest.test_content)} className="btn btn-secondary btn-sm">
                                    <Download size={15} /> Markdown
                                </button>
                                <button
                                    onClick={handleDownloadFromBackend}
                                    disabled={!generatedTest?.savedFileId}
                                    className="btn btn-secondary btn-sm"
                                >
                                    <FileDown size={15} /> PDF
                                </button>
                                <button onClick={handleSaveAndDownload} className="btn btn-primary btn-sm">
                                    <Save size={15} /> Сохранить и скачать
                                </button>
                                <button onClick={handleSendToGoogleForm} className="btn btn-warning btn-sm">
                                    <ExternalLink size={15} /> Google Форма
                                </button>
                            </div>

                            {googleFormStatus === "success" && (
                                <div className="ct-status success">Google Форма создана!</div>
                            )}
                            {googleFormStatus === "error" && (
                                <div className="ct-status error">Ошибка создания формы</div>
                            )}

                            {generatedTest?.googleFormUrl && (
                                <a
                                    href={generatedTest.googleFormUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn btn-primary btn-sm"
                                    style={{ marginTop: 8 }}
                                >
                                    <ExternalLink size={15} /> Открыть Google Форму
                                </a>
                            )}

                            {generatedTest?.savedFileId && (
                                <div className="ct-status success">
                                    Тест сохранён! ID: {generatedTest.savedFileId}
                                </div>
                            )}

                            <div className="ct-test-content">
                                <pre>{generatedTest.test_content}</pre>
                            </div>
                        </div>
                    )}
                </>
            )}

            {activeTab === "prompt" && (
                <div className="ct-panel">
                    <h3 className="ct-panel-title">Генерация материала и теста по промпту</h3>
                    <p className="ct-prompt-hint">
                        Опишите, какой материал и тест вы хотите получить. Агент сгенерирует учебный материал,
                        сохранит его в ваши документы и сразу сделает по нему тест.
                    </p>

                    <div className="ct-field">
                        <label htmlFor="prompt-input">Запрос</label>
                        <div className="ct-prompt-wrap">
                            <textarea
                                id="prompt-input"
                                value={promptText + (interimTranscript ? ` ${interimTranscript}` : "")}
                                onChange={(e) => setPromptText(e.target.value)}
                                rows={4}
                                className="form-control"
                                placeholder="Например: Хочу создать тест для 8 класса по биологии на тему «Клетка»"
                                disabled={isGeneratingFromPrompt}
                            />
                            <div className="ct-prompt-controls">
                                <select
                                    value={speechLang}
                                    onChange={(e) => setSpeechLang(e.target.value)}
                                    className="form-control ct-lang-select"
                                    disabled={isListening}
                                    title="Язык распознавания"
                                >
                                    <option value="ru-RU">Русский</option>
                                    <option value="en-US">English</option>
                                </select>
                                <button
                                    type="button"
                                    onClick={toggleListening}
                                    disabled={!speechSupported || isGeneratingFromPrompt}
                                    className={`btn btn-sm ${isListening ? "btn-danger" : "btn-secondary"}`}
                                    title={speechSupported ? "Голосовой ввод" : "Голосовой ввод не поддерживается"}
                                >
                                    {isListening ? <><MicOff size={14} /> Стоп</> : <><Mic size={14} /> Голосом</>}
                                </button>
                            </div>
                        </div>
                        {!speechSupported && (
                            <div className="ct-warning">
                                <AlertTriangle size={14} />
                                <span>Голосовой ввод работает в Chrome/Edge.</span>
                            </div>
                        )}
                        {speechError && (
                            <div className="ct-status error">Ошибка распознавания: {speechError}</div>
                        )}
                    </div>

                    <div className="ct-grid">
                        <div className="ct-field">
                            <label htmlFor="prompt-question-count">Количество вопросов</label>
                            <input
                                id="prompt-question-count"
                                type="number"
                                min="1"
                                max="50"
                                value={testParams.questionCount}
                                onChange={(e) =>
                                    setTestParams((prev) => ({ ...prev, questionCount: parseInt(e.target.value) }))
                                }
                                className="form-control"
                            />
                        </div>
                        <div className="ct-field">
                            <label htmlFor="prompt-difficulty">Сложность</label>
                            <select
                                id="prompt-difficulty"
                                value={testParams.difficulty}
                                onChange={(e) =>
                                    setTestParams((prev) => ({ ...prev, difficulty: e.target.value }))
                                }
                                className="form-control"
                            >
                                {difficultyLevels.map((level) => (
                                    <option key={level.value} value={level.value}>{level.label}</option>
                                ))}
                            </select>
                        </div>
                        <div className="ct-field">
                            <label htmlFor="prompt-question-type">Тип вопросов</label>
                            <select
                                id="prompt-question-type"
                                value={testParams.questionType}
                                onChange={(e) =>
                                    setTestParams((prev) => ({ ...prev, questionType: e.target.value }))
                                }
                                className="form-control"
                            >
                                {questionTypes.map((type) => (
                                    <option key={type.value} value={type.value}>{type.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <label className="ct-checkbox">
                        <input
                            type="checkbox"
                            checked={testParams.includeAnswers}
                            onChange={(e) =>
                                setTestParams((prev) => ({ ...prev, includeAnswers: e.target.checked }))
                            }
                        />
                        <span>Включать ответы</span>
                    </label>

                    <button
                        onClick={generateFromPrompt}
                        disabled={isGeneratingFromPrompt || promptText.trim().length < 3}
                        className="btn btn-primary ct-generate-btn"
                    >
                        {isGeneratingFromPrompt ? (
                            <><Loader2 size={18} className="spin" /> Генерация...</>
                        ) : (
                            <><Sparkles size={18} /> Сгенерировать материал и тест</>
                        )}
                    </button>

                    {promptGenerationStatus && (
                        <div className={`ct-status ${promptGenerationStatus.startsWith("Ошибка") ? "error" : "success"}`}>
                            {promptGenerationStatus}
                        </div>
                    )}
                </div>
            )}

            {activeTab === "saved" && (
                <div className="ct-saved">
                    <div className="ct-saved-header">
                        <h3>Сохранённые тесты</h3>
                        <button onClick={loadSavedTests} className="btn btn-secondary btn-sm">
                            <RefreshCw size={14} /> Обновить
                        </button>
                    </div>

                    {savedTests.length === 0 ? (
                        <div className="ct-empty">
                            <p>Нет сохранённых тестов</p>
                        </div>
                    ) : (
                        <div className="ct-saved-list">
                            {savedTests.map((test) => (
                                <div key={test.id} className="ct-saved-item">
                                    <div className="ct-saved-info">
                                        <h4>{test.filename}</h4>
                                        <p>
                                            ID: {test.id} &middot; Документ: {getDocumentName(test.document_id)} &middot; {formatDate(test.upload_timestamp)}
                                        </p>
                                    </div>
                                    <div className="ct-saved-actions">
                                        <button
                                            onClick={() => downloadTestFromBackend(test.id, test.filename.replace(".md", ".pdf"))}
                                            className="btn btn-secondary btn-sm"
                                        >
                                            <Download size={14} /> Скачать
                                        </button>
                                        <button
                                            onClick={() => deleteTest(test.id, test.filename)}
                                            className="btn btn-danger btn-sm"
                                        >
                                            <Trash2 size={14} /> Удалить
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

export default CreateTest;
