import React, { useState, useEffect } from "react";
import { documentAPI } from "../../services/api";
import {
	Upload,
	Trash2,
	Download,
	RefreshCw,
	FileText,
	AlertTriangle,
	Loader2,
} from "lucide-react";
import "./MyDocuments.css";

const MyDocuments = () => {
	const [documents, setDocuments] = useState([]);
	const [selectedFile, setSelectedFile] = useState(null);
	const [uploadStatus, setUploadStatus] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [isUploading, setIsUploading] = useState(false);
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
			if (isConnected) loadDocuments();
		};
		initialize();
	}, []);

	const loadDocuments = async () => {
		try {
			setIsLoading(true);
			const docs = await documentAPI.getDocuments();
			setDocuments(docs);
		} catch (error) {
			console.error("Error loading documents:", error);
			setUploadStatus(`Ошибка: ${error.message}`);
			setConnectionError(true);
		} finally {
			setIsLoading(false);
		}
	};

	const handleDownloadDocument = async (fileId, filename) => {
		try {
			await documentAPI.downloadDocument(fileId, filename);
			setUploadStatus(`Документ "${filename}" скачан`);
		} catch (error) {
			console.error("Error downloading document:", error);
			setUploadStatus(`Ошибка при скачивании: ${error.message}`);
		}
	};

	const handleFileSelect = (e) => {
		const file = e.target.files[0];
		if (file) {
			setSelectedFile(file);
			setUploadStatus("");
		}
	};

	const handleUpload = async () => {
		if (!selectedFile) {
			setUploadStatus("Выберите файл");
			return;
		}
		setIsUploading(true);
		setUploadStatus("Загрузка...");
		try {
			const uniquenessCheck = await documentAPI.checkUniqueness(selectedFile);
			if (!uniquenessCheck.is_unique) {
				setUploadStatus(
					`Документ уже существует: ${uniquenessCheck.message || uniquenessCheck.detail}`,
				);
				return;
			}
			const result = await documentAPI.uploadDocument(selectedFile);
			setUploadStatus(`"${selectedFile.name}" загружен! ID: ${result.file_id}`);
			setSelectedFile(null);
			const fileInput = document.getElementById("file-input");
			if (fileInput) fileInput.value = "";
			await loadDocuments();
		} catch (error) {
			console.error("Error uploading document:", error);
			setUploadStatus(
				`Ошибка: ${error.response?.data?.detail || error.message}`,
			);
		} finally {
			setIsUploading(false);
		}
	};

	const handleDelete = async (fileId, filename) => {
		if (!window.confirm(`Удалить документ "${filename}"?`)) return;
		try {
			await documentAPI.deleteDocument(fileId);
			setUploadStatus(`"${filename}" удалён`);
			await loadDocuments();
		} catch (error) {
			console.error("Error deleting document:", error);
			setUploadStatus(
				`Ошибка: ${error.response?.data?.detail || error.message}`,
			);
		}
	};

	const formatDate = (dateString) =>
		new Date(dateString).toLocaleString("ru-RU");

	return (
		<div className="docs-page">
			{connectionError && (
				<div className="docs-conn-error">
					<AlertTriangle size={20} />
					<div>
						<strong>Нет подключения к серверу</strong>
						<p>Убедитесь, что бэкенд запущен на localhost:8001</p>
					</div>
					<button
						onClick={checkBackendConnection}
						className="btn btn-warning btn-sm"
					>
						Проверить
					</button>
				</div>
			)}

			<div className="docs-upload-card">
				<h3>Загрузить документ</h3>
				<div className="docs-upload-area">
					<input
						id="file-input"
						type="file"
						accept=".pdf,.docx,.html,.txt"
						onChange={handleFileSelect}
						className="form-control"
					/>
					{selectedFile && (
						<div className="docs-file-info">
							<FileText size={16} />
							<span>
								{selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
							</span>
						</div>
					)}
					<button
						onClick={handleUpload}
						disabled={!selectedFile || isUploading}
						className="btn btn-primary"
					>
						{isUploading ? (
							<>
								<Loader2 size={16} className="spin" /> Загрузка...
							</>
						) : (
							<>
								<Upload size={16} /> Загрузить
							</>
						)}
					</button>
				</div>
				{uploadStatus && (
					<div
						className={`docs-status ${uploadStatus.includes("Ошибка") ? "error" : "success"}`}
					>
						{uploadStatus}
					</div>
				)}
				<p className="docs-formats">Форматы: PDF, DOCX</p>
			</div>

			<div className="docs-list-card">
				<div className="docs-list-header">
					<h3>Документы ({documents.length})</h3>
					<button
						onClick={loadDocuments}
						className="btn btn-secondary btn-sm"
						disabled={isLoading}
					>
						<RefreshCw size={14} /> Обновить
					</button>
				</div>

				{isLoading && documents.length === 0 ? (
					<div className="docs-loading">Загрузка...</div>
				) : documents.length === 0 ? (
					<div className="docs-empty">
						<FileText size={32} />
						<p>Нет загруженных документов</p>
						<p className="docs-empty-sub">
							Загрузите документ, чтобы создавать тесты
						</p>
					</div>
				) : (
					<div className="docs-grid">
						{documents.map((doc) => (
							<div key={doc.id} className="docs-item">
								<div className="docs-item-icon">
									<FileText size={20} />
								</div>
								<div className="docs-item-info">
									<h4>{doc.filename}</h4>
									<span>
										ID: {doc.id} &middot; {formatDate(doc.upload_timestamp)}
									</span>
								</div>
								<div className="docs-item-actions">
									<button
										onClick={() => handleDownloadDocument(doc.id, doc.filename)}
										className="btn btn-secondary btn-sm"
									>
										<Download size={14} /> Скачать
									</button>
									<button
										onClick={() => handleDelete(doc.id, doc.filename)}
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
		</div>
	);
};

export default MyDocuments;
