import React, { useState, useEffect } from "react";
import { testPDFAPI } from "../../services/api";
import {
	Download,
	Trash2,
	RefreshCw,
	ClipboardCheck,
	AlertTriangle,
	X,
} from "lucide-react";
import "./MyTests.css";

const MyTests = () => {
	const [tests, setTests] = useState([]);
	const [isLoading, setIsLoading] = useState(false);
	const [selectedTest, setSelectedTest] = useState(null);
	const [connectionError, setConnectionError] = useState(false);

	const checkBackendConnection = async () => {
		try {
			const response = await fetch("http://localhost:8001/health");
			if (response.ok) {
				setConnectionError(false);
				return true;
			}
		} catch (error) {
			console.error("Backend connection failed:", error);
			setConnectionError(true);
			return false;
		}
		return false;
	};

	useEffect(() => {
		const initialize = async () => {
			const isConnected = await checkBackendConnection();
			if (isConnected) loadTests();
		};
		initialize();
	}, []);

	const loadTests = async () => {
		try {
			setIsLoading(true);
			const testList = await testPDFAPI.getTestPDFs();
			setTests(testList);
		} catch (error) {
			console.error("Error loading tests:", error);
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
			if (selectedTest?.id === testId) setSelectedTest(null);
		} catch (error) {
			console.error("Error deleting test:", error);
			alert(`Ошибка: ${error.message}`);
		}
	};

	const handleDownload = async (testId, filename) => {
		try {
			const pdfBlob = await testPDFAPI.downloadTestPDF(testId);
			const url = URL.createObjectURL(pdfBlob);
			const a = document.createElement("a");
			a.href = url;
			a.download = filename;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		} catch (error) {
			console.error("Error downloading test:", error);
			alert(`Ошибка: ${error.message}`);
		}
	};

	const formatDate = (dateString) =>
		new Date(dateString).toLocaleString("ru-RU");

	return (
		<div className="tests-page">
			{connectionError && (
				<div className="tests-conn-error">
					<AlertTriangle size={20} />
					<div>
						<strong>Нет подключения к серверу</strong>
						<p>Убедитесь, что бэкенд запущен</p>
					</div>
					<button
						onClick={checkBackendConnection}
						className="btn btn-warning btn-sm"
					>
						Проверить
					</button>
				</div>
			)}

			<div className="tests-layout">
				<div className="tests-list-card">
					<div className="tests-list-header">
						<h3>Тесты ({tests.length})</h3>
						<button
							onClick={loadTests}
							className="btn btn-secondary btn-sm"
							disabled={isLoading}
						>
							<RefreshCw size={14} /> Обновить
						</button>
					</div>

					{isLoading && tests.length === 0 ? (
						<div className="tests-loading">Загрузка тестов...</div>
					) : tests.length === 0 ? (
						<div className="tests-empty">
							<ClipboardCheck size={32} />
							<p>Нет созданных тестов</p>
							<p className="tests-empty-sub">Перейдите в «Создать тест»</p>
						</div>
					) : (
						<div className="tests-grid">
							{tests.map((test) => (
								<div
									key={test.id}
									className={`tests-item ${selectedTest?.id === test.id ? "selected" : ""}`}
									onClick={() => setSelectedTest(test)}
								>
									<div className="tests-item-info">
										<h4>{test.filename}</h4>
										<span>
											ID: {test.id} &middot; {formatDate(test.upload_timestamp)}
											{test.document_id && ` · Док: ${test.document_id}`}
										</span>
									</div>
									<div className="tests-item-actions">
										<button
											onClick={(e) => {
												e.stopPropagation();
												handleDownload(test.id, test.filename);
											}}
											className="btn btn-secondary btn-sm"
										>
											<Download size={14} />
										</button>
										<button
											onClick={(e) => {
												e.stopPropagation();
												handleDelete(test.id, test.filename);
											}}
											className="btn btn-danger btn-sm"
										>
											<Trash2 size={14} />
										</button>
									</div>
								</div>
							))}
						</div>
					)}
				</div>

				{selectedTest && (
					<div className="tests-preview">
						<div className="tests-preview-header">
							<h3>Детали</h3>
							<button
								onClick={() => setSelectedTest(null)}
								className="tests-preview-close"
							>
								<X size={18} />
							</button>
						</div>
						<div className="tests-preview-body">
							<h4>{selectedTest.filename}</h4>
							<div className="tests-detail-rows">
								<div>
									<strong>ID:</strong> {selectedTest.id}
								</div>
								<div>
									<strong>Создан:</strong>{" "}
									{formatDate(selectedTest.upload_timestamp)}
								</div>
								{selectedTest.document_id && (
									<div>
										<strong>Документ:</strong> {selectedTest.document_id}
									</div>
								)}
								{selectedTest.session_id && (
									<div>
										<strong>Сессия:</strong> {selectedTest.session_id}
									</div>
								)}
							</div>
							<div className="tests-preview-actions">
								<button
									onClick={() =>
										handleDownload(selectedTest.id, selectedTest.filename)
									}
									className="btn btn-primary"
								>
									<Download size={16} /> Скачать
								</button>
								<button
									onClick={() =>
										handleDelete(selectedTest.id, selectedTest.filename)
									}
									className="btn btn-danger"
								>
									<Trash2 size={16} /> Удалить
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
