import React, { useState, useEffect } from "react";
import { documentAPI, testGenerationAPI, testPDFAPI } from "../../services/api";
import { googleFormAPI } from "../../services/googleFormAPI";
import "./CreateTest.css";

const CreateTest = () => {
	const [documents, setDocuments] = useState([]);
	const [googleFormStatus, setGoogleFormStatus] = useState("");

	// Отправка теста в Google Apps Script
	const handleSendToGoogleForm = async () => {
		if (!generatedTest || !generatedTest.test_content) {
			alert("Нет сгенерированного теста для отправки");
			return;
		}
		setGoogleFormStatus("Отправка...");
		try {
			// Парсим JSON теста
			const testJson = JSON.parse(generatedTest.test_content);

			const result = await googleFormAPI.sendTestToGoogleForm(testJson);

			// Новый код — берём ответ от Apps Script
			const scriptResp = result.script_response || result; // на случай если структура изменится

			if (scriptResp.success && scriptResp.formUrl) {
				setGoogleFormStatus(
					`✅ Google Форма создана!\n\n` +
						`<strong>Ссылка:</strong> <a href="${scriptResp.formUrl}" target="_blank" rel="noopener noreferrer">📝 Открыть форму</a>`,
				);

				// Дополнительно можно сохранить ссылку в состояние
				setGeneratedTest((prev) => ({
					...prev,
					googleFormUrl: scriptResp.formUrl,
				}));
			}
		} catch (error) {
			setGoogleFormStatus("❌ Ошибка при отправке в Google Apps Script");
			alert("Ошибка при отправке в Google Apps Script: " + error.message);
		}
	};
	const [selectedDocument, setSelectedDocument] = useState("");
	const [testParams, setTestParams] = useState({
		questionCount: 10,
		difficulty: "Для средних классов",
		questionType: "multiple_choice",
		includeAnswers: true,
		model: "lakomoor/vikhr-llama-3.2-1b-instruct:1b",
		// XML fields removed
	});
	const [generatedTest, setGeneratedTest] = useState(null);
	const [isGenerating, setIsGenerating] = useState(false);
	const [savedTests, setSavedTests] = useState([]);
	const [activeTab, setActiveTab] = useState("generate");

	// Новые состояния для загрузки документа
	const [newDocumentFile, setNewDocumentFile] = useState(null);
	const [isUploadingDocument, setIsUploadingDocument] = useState(false);
	const [uploadDocumentStatus, setUploadDocumentStatus] = useState("");
	const [showUploadForm, setShowUploadForm] = useState(false);

	console.log("🎯 CreateTest component rendered");

	const difficultyLevels = [
		{ value: "Для начальных классов", label: "🟢 Для начальных классов" },
		{ value: "Для средних классов", label: "🟡 Для средних классов" },
		{ value: "Для старших классов", label: "🔴 Для старших классов" },
		{ value: "Для студентов", label: "🎓 Для студентов" },
	];

	const questionTypes = [
		{ value: "multiple_choice", label: "📋 Множественный выбор" },
		{ value: "open_questions", label: "📝 Открытые вопросы" },
	];

	const models = [
		{ value: "lakomoor/vikhr-llama-3.2-1b-instruct:1b", label: "🦙 Llama 3.2" },
	];

	useEffect(() => {
		console.log("🏁 CreateTest mounted, loading data...");
		loadDocuments();
		loadSavedTests();
	}, []);

	const loadDocuments = async () => {
		try {
			const docs = await documentAPI.getDocuments();
			setDocuments(docs);
			console.log("✅ Documents loaded:", docs.length);
		} catch (error) {
			console.error("Error loading documents:", error);
			alert(`Ошибка при загрузке документов: ${error.message}`);
		}
	};

	const loadSavedTests = async () => {
		try {
			const tests = await testPDFAPI.getTestPDFs();
			setSavedTests(tests);
			console.log("✅ Tests loaded:", tests.length);
		} catch (error) {
			console.error("Error loading saved tests:", error);
		}
	};

	// Функция для загрузки нового документа
	const handleUploadNewDocument = async () => {
		if (!newDocumentFile) {
			setUploadDocumentStatus("Пожалуйста, выберите файл");
			return;
		}

		setIsUploadingDocument(true);
		setUploadDocumentStatus("Загрузка...");

		try {
			// Сначала проверяем уникальность
			const uniquenessCheck =
				await documentAPI.checkUniqueness(newDocumentFile);

			if (!uniquenessCheck.is_unique) {
				setUploadDocumentStatus(
					`Документ не уникален: ${uniquenessCheck.message || uniquenessCheck.detail}`,
				);
				return;
			}

			// Загружаем документ
			const result = await documentAPI.uploadDocument(newDocumentFile);
			setUploadDocumentStatus(
				`Документ "${newDocumentFile.name}" успешно загружен! ID: ${result.file_id}`,
			);
			setNewDocumentFile(null);

			// Очищаем input файла
			const fileInput = document.getElementById("new-document-file-input");
			if (fileInput) fileInput.value = "";

			// Обновляем список документов
			await loadDocuments();

			// Автоматически выбираем новый документ
			setSelectedDocument(result.file_id.toString());

			// Скрываем форму загрузки
			setShowUploadForm(false);
		} catch (error) {
			console.error("Error uploading document:", error);
			setUploadDocumentStatus(
				`Ошибка при загрузке документа: ${error.response?.data?.detail || error.message}`,
			);
		} finally {
			setIsUploadingDocument(false);
		}
	};

	// Функция для выбора файла
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
			alert(
				"Генерация занимает больше времени, чем ожидалось. Пожалуйста, подождите... Это может занять несколько минут для больших документов.",
			);
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

			console.log("📤 Sending request data:", requestData);

			const result = await testGenerationAPI.generateTest(requestData);
			console.log("📥 Received result:", result);
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

	// Функция для скачивания через бэкенд
	const downloadTestFromBackend = async (
		fileId,
		filename = `test_${Date.now()}.pdf`,
	) => {
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

			console.log(`Тест ${filename} успешно скачан через бэкенд`);
			return { success: true, filename };
		} catch (error) {
			console.error("Error downloading test from backend:", error);
			alert(`Ошибка при скачивании теста: ${error.message}`);
			throw error;
		}
	};

	// Обновленная функция saveTest чтобы возвращать file_id
	const saveTest = async () => {
		if (!generatedTest) {
			alert("Нет сгенерированного теста для сохранения");
			return;
		}

		try {
			const filename = `test_${Date.now()}.md`;
			const documentId = selectedDocument ? parseInt(selectedDocument) : null;
			const sessionId = generatedTest.session_id || `session_${Date.now()}`;

			// Показываем уведомление о начале сохранения
			setIsGenerating(true);
			const saveButton = document.querySelector(".btn-success");
			if (saveButton) {
				saveButton.textContent = "💾 Сохранение...";
				saveButton.disabled = true;
			}

			// Используем основной метод сохранения
			const result = await testGenerationAPI.saveTest(
				generatedTest.test_content,
				filename,
				documentId,
				sessionId,
			);

			// Сохраняем информацию для последующего скачивания
			const savedTestWithId = {
				...generatedTest,
				savedFileId: result.file_id,
				savedFilename: result.filename || filename.replace(".md", ".pdf"),
			};
			setGeneratedTest(savedTestWithId);

			// Восстанавливаем кнопку
			if (saveButton) {
				saveButton.textContent = "💾 Сохранить тест";
				saveButton.disabled = false;
			}

			setIsGenerating(false);

			// Показываем успешное сообщение
			alert(
				`✅ Тест успешно сохранен!\nID: ${result.file_id}\nФайл: ${result.filename}`,
			);

			// Обновляем список сохраненных тестов
			await loadSavedTests();
		} catch (error) {
			console.error("❌ Error saving test:", error);

			// Восстанавливаем кнопку в случае ошибки
			const saveButton = document.querySelector(".btn-success");
			if (saveButton) {
				saveButton.textContent = "💾 Сохранить тест";
				saveButton.disabled = false;
			}

			setIsGenerating(false);

			// Более информативное сообщение об ошибке
			let errorMessage = "Ошибка при сохранении теста";
			if (error.message.includes("timeout")) {
				errorMessage =
					"Превышено время ожидания при сохранении. Попробуйте еще раз.";
			} else if (error.message.includes("Network Error")) {
				errorMessage =
					"Проблемы с подключением к серверу. Проверьте интернет-соединение.";
			} else {
				errorMessage = `Ошибка: ${error.message}`;
			}

			alert(errorMessage);
		}
	};

	// Функция для скачивания через бэкенд
	const handleDownloadFromBackend = async () => {
		if (!generatedTest?.savedFileId) {
			alert("Сначала сохраните тест, чтобы скачать через бэкенд");
			return;
		}

		try {
			await downloadTestFromBackend(
				generatedTest.savedFileId,
				generatedTest.savedFilename.replace(".md", ".pdf"),
			);
		} catch (error) {
			console.error("Error downloading from backend:", error);
		}
	};

	// Функция для прямого сохранения и скачивания
	const handleSaveAndDownload = async () => {
		if (!generatedTest) {
			alert("Нет сгенерированного теста");
			return;
		}

		try {
			const filename = `test_${Date.now()}.md`;
			const documentId = selectedDocument ? parseInt(selectedDocument) : null;
			const sessionId = generatedTest.session_id || `session_${Date.now()}`;

			// Показываем уведомление о начале процесса
			setIsGenerating(true);
			const saveDownloadButton = document.querySelector(".btn-info");
			if (saveDownloadButton) {
				saveDownloadButton.textContent = "💾📥 Сохранение...";
				saveDownloadButton.disabled = true;
			}

			// Сохраняем тест
			const result = await testGenerationAPI.saveTest(
				generatedTest.test_content,
				filename,
				documentId,
				sessionId,
			);

			// Сразу скачиваем через бэкенд
			await downloadTestFromBackend(result.file_id, result.filename);

			// Восстанавливаем кнопку
			if (saveDownloadButton) {
				saveDownloadButton.textContent = "💾📥 Сохранить и скачать";
				saveDownloadButton.disabled = false;
			}

			setIsGenerating(false);

			alert("✅ Тест успешно сохранен и скачан!");
			await loadSavedTests();
		} catch (error) {
			console.error("❌ Error in save and download:", error);

			// Восстанавливаем кнопку
			const saveDownloadButton = document.querySelector(".btn-info");
			if (saveDownloadButton) {
				saveDownloadButton.textContent = "💾📥 Сохранить и скачать";
				saveDownloadButton.disabled = false;
			}

			setIsGenerating(false);

			alert(`Ошибка: ${error.message}`);
		}
	};

	// Клиентское скачивание (старое)
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
			alert("Тест удален");
		} catch (error) {
			console.error("Error deleting test:", error);
			alert(`Ошибка при удалении теста: ${error.message}`);
		}
	};

	const formatDate = (dateString) => {
		return new Date(dateString).toLocaleString("ru-RU");
	};

	const getDocumentName = (documentId) => {
		const doc = documents.find((d) => d.id === documentId);
		return doc ? doc.filename : "Не указан";
	};

	return (
		<div className="create-test">
			<h2>Генератор тестов</h2>

			<div className="tabs">
				<button
					className={`tab ${activeTab === "generate" ? "active" : ""}`}
					onClick={() => setActiveTab("generate")}
					title="Перейти к генерации теста"
				>
					📝 Генерация теста
				</button>
				<button
					className={`tab ${activeTab === "saved" ? "active" : ""}`}
					onClick={() => setActiveTab("saved")}
					title="Просмотреть сохраненные тесты"
				>
					💾 Сохраненные тесты ({savedTests.length})
				</button>
			</div>

			{activeTab === "generate" && (
				<>
					<div className="params-panel card">
						<h3>Основные параметры теста</h3>

						<div className="params-grid">
							<div className="form-group">
								<label htmlFor="document-select">
									Документ для тестирования:
									<span className="optional"> (обязательно)</span>
								</label>

								{/* Выбор существующего документа */}
								<select
									id="document-select"
									value={selectedDocument}
									onChange={(e) => setSelectedDocument(e.target.value)}
									className="form-control"
									title="Выберите документ для генерации теста"
									aria-label="Выберите документ для генерации теста"
								>
									<option value="">Выберите документ...</option>
									{documents.map((doc) => (
										<option key={doc.id} value={doc.id}>
											{doc.filename} (ID: {doc.id})
										</option>
									))}
								</select>

								{/* Кнопка для показа формы загрузки */}
								<div className="upload-document-section">
									<button
										type="button"
										onClick={() => setShowUploadForm(!showUploadForm)}
										className="btn btn-outline-secondary btn-sm"
										style={{ marginTop: "10px" }}
									>
										{showUploadForm
											? "✖ Отменить загрузку"
											: "📤 Загрузить новый документ"}
									</button>

									{/* Форма загрузки нового документа */}
									{showUploadForm && (
										<div
											className="new-document-upload"
											style={{
												marginTop: "15px",
												padding: "15px",
												border: "1px solid #ddd",
												borderRadius: "8px",
												backgroundColor: "#f8f9fa",
											}}
										>
											<h5>Загрузка нового документа</h5>

											<div className="upload-area">
												<input
													id="new-document-file-input"
													type="file"
													accept=".pdf,.docx,.html,.txt"
													onChange={handleNewDocumentFileSelect}
													className="form-control"
													style={{ marginBottom: "10px" }}
												/>

												{newDocumentFile && (
													<div
														className="selected-file-info"
														style={{
															padding: "10px",
															backgroundColor: "#e9f7ef",
															borderRadius: "4px",
															marginBottom: "10px",
															borderLeft: "4px solid #28a745",
														}}
													>
														<strong>Выбран файл:</strong> {newDocumentFile.name}
														<br />
														<small>
															Размер: {Math.round(newDocumentFile.size / 1024)}{" "}
															KB
														</small>
													</div>
												)}

												<button
													onClick={handleUploadNewDocument}
													disabled={!newDocumentFile || isUploadingDocument}
													className="btn btn-primary btn-sm"
													style={{ marginRight: "10px" }}
												>
													{isUploadingDocument
														? "🔄 Загрузка..."
														: "📤 Загрузить"}
												</button>

												<button
													type="button"
													onClick={() => {
														setShowUploadForm(false);
														setNewDocumentFile(null);
														setUploadDocumentStatus("");
													}}
													className="btn btn-secondary btn-sm"
												>
													Отмена
												</button>
											</div>

											{uploadDocumentStatus && (
												<div
													className={`upload-status ${uploadDocumentStatus.includes("Ошибка") ? "error" : "success"}`}
													style={{
														marginTop: "10px",
														padding: "10px",
														borderRadius: "4px",
														fontSize: "0.9em",
													}}
												>
													{uploadDocumentStatus}
												</div>
											)}

											<div
												className="supported-formats-info"
												style={{
													marginTop: "10px",
													fontSize: "0.8em",
													color: "#666",
												}}
											>
												<strong>Поддерживаемые форматы:</strong> PDF, DOCX
											</div>
										</div>
									)}
								</div>

								<div
									className="document-help"
									style={{ fontSize: "0.8em", color: "#666", marginTop: "5px" }}
								>
									{selectedDocument
										? `Выбран документ: ${documents.find((d) => d.id == selectedDocument)?.filename}`
										: "Выберите документ из списка или загрузите новый"}
								</div>
							</div>

							<div className="form-group">
								<label htmlFor="total-question-count">
									Количество вопросов:
								</label>
								<input
									id="total-question-count"
									type="number"
									min="1"
									max="50"
									value={testParams.questionCount}
									onChange={(e) =>
										setTestParams((prev) => ({
											...prev,
											questionCount: parseInt(e.target.value),
										}))
									}
									className="form-control"
									title="Количество вопросов в тесте от 1 до 50"
									aria-label="Количество вопросов в тесте"
									placeholder="Введите число от 1 до 50"
								/>
							</div>

							<div className="form-group">
								<label htmlFor="difficulty-select">Сложность:</label>
								<select
									id="difficulty-select"
									value={testParams.difficulty}
									onChange={(e) =>
										setTestParams((prev) => ({
											...prev,
											difficulty: e.target.value,
										}))
									}
									className="form-control"
									title="Уровень сложности теста"
									aria-label="Выберите уровень сложности теста"
								>
									{difficultyLevels.map((level) => (
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
									onChange={(e) =>
										setTestParams((prev) => ({
											...prev,
											questionType: e.target.value,
										}))
									}
									className="form-control"
									title="Тип генерируемых вопросов"
									aria-label="Выберите тип вопросов"
								>
									{questionTypes.map((type) => (
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
									onChange={(e) =>
										setTestParams((prev) => ({
											...prev,
											model: e.target.value,
										}))
									}
									className="form-control"
									title="Модель ИИ для генерации вопросов"
									aria-label="Выберите модель искусственного интеллекта"
								>
									{models.map((model) => (
										<option key={model.value} value={model.value}>
											{model.label}
										</option>
									))}
								</select>
							</div>
						</div>

						<div className="form-check">
							<input
								type="checkbox"
								checked={testParams.includeAnswers}
								onChange={(e) =>
									setTestParams((prev) => ({
										...prev,
										includeAnswers: e.target.checked,
									}))
								}
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
							disabled={isGenerating || !selectedDocument}
							className="btn btn-primary generate-btn"
							title="Сгенерировать тест с выбранными параметрами"
							aria-label="Сгенерировать тест"
						>
							{isGenerating ? "🔄 Генерация..." : "⚡ Сгенерировать тест"}
						</button>

						{documents.length === 0 && (
							<div className="warning-message">
								⚠️ Для генерации тестов необходимо загрузить документ
							</div>
						)}
					</div>

					{generatedTest && (
						<div className="test-result card">
							<div className="result-header">
								<h3>Сгенерированный тест</h3>
								<div className="result-stats">
									<p>📊 Всего вопросов: {testParams.questionCount}</p>
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

									<button
										onClick={handleDownloadFromBackend}
										disabled={!generatedTest?.savedFileId}
										className="btn btn-primary"
										title="Скачать тест через бэкенд в формате PDF"
										aria-label="Скачать тест через бэкенд"
									>
										📄 Скачать PDF (бэкенд)
									</button>

									<button
										onClick={handleSaveAndDownload}
										className="btn btn-info"
										title="Сохранить и сразу скачать через бэкенд"
										aria-label="Сохранить и скачать"
									>
										💾📥 Сохранить и скачать
									</button>

									{/* Кнопка для Google Формы */}
									<button
										onClick={handleSendToGoogleForm}
										className="btn btn-warning"
										title="Создать Google Форму из теста"
										aria-label="Создать Google Форму"
										style={{ marginLeft: "10px" }}
									>
										🟨 Создать Google Форму
									</button>
								</div>
								{googleFormStatus && (
									<div
										className="google-form-status"
										style={{
											marginTop: "10px",
											color: googleFormStatus.startsWith("✅")
												? "green"
												: "red",
										}}
									>
										{googleFormStatus}
									</div>
								)}
								{generatedTest?.googleFormUrl && (
									<div style={{ marginTop: "15px" }}>
										<a
											href={generatedTest.googleFormUrl}
											target="_blank"
											rel="noopener noreferrer"
											className="btn btn-success"
											style={{ fontSize: "1.1em", padding: "12px 24px" }}
										>
											Открыть Google Форму
										</a>
									</div>
								)}

								{/* Информация о сохраненном тесте */}
								{generatedTest?.savedFileId && (
									<div
										className="saved-test-info"
										style={{
											marginTop: "10px",
											padding: "10px",
											backgroundColor: "#e9f7ef",
											borderRadius: "4px",
											borderLeft: "4px solid #28a745",
										}}
									>
										<strong>Тест сохранен!</strong> ID:{" "}
										{generatedTest.savedFileId}
										<br />
										<small>Теперь можно скачать через бэкенд эндпоинт</small>
									</div>
								)}
							</div>

							<div className="test-content">
								<pre>{generatedTest.test_content}</pre>
							</div>
						</div>
					)}
				</>
			)}

			{activeTab === "saved" && (
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
							{savedTests.map((test) => (
								<div key={test.id} className="test-item">
									<div className="test-info">
										<h4>{test.filename}</h4>
										<p className="test-meta">
											ID: {test.id} | Документ:{" "}
											{getDocumentName(test.document_id)} | Создан:{" "}
											{formatDate(test.upload_timestamp)}
										</p>
									</div>
									<div className="test-actions">
										<button
											onClick={() =>
												downloadTestFromBackend(
													test.id,
													test.filename.replace(".md", ".pdf"),
												)
											}
											className="btn btn-secondary btn-sm"
											title="Скачать тест через бэкенд"
											aria-label={`Скачать тест ${test.filename}`}
										>
											📥 Скачать PDF
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

export default CreateTest;
