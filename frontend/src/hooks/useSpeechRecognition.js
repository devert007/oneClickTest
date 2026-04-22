import { useCallback, useEffect, useRef, useState } from "react";

const getRecognitionClass = () =>
	window.SpeechRecognition || window.webkitSpeechRecognition || null;

export const isSpeechRecognitionSupported = () => !!getRecognitionClass();

export default function useSpeechRecognition({ lang = "ru-RU", onResult } = {}) {
	const [isListening, setIsListening] = useState(false);
	const [error, setError] = useState(null);
	const [interimTranscript, setInterimTranscript] = useState("");
	const recognitionRef = useRef(null);
	const onResultRef = useRef(onResult);

	useEffect(() => {
		onResultRef.current = onResult;
	}, [onResult]);

	const stop = useCallback(() => {
		if (recognitionRef.current) {
			try {
				recognitionRef.current.stop();
			} catch {
				// noop
			}
		}
		setIsListening(false);
	}, []);

	const start = useCallback(() => {
		const SpeechRecognitionClass = getRecognitionClass();
		if (!SpeechRecognitionClass) {
			setError("Голосовой ввод не поддерживается этим браузером. Используйте Chrome или Edge.");
			return;
		}

		if (recognitionRef.current) {
			try {
				recognitionRef.current.stop();
			} catch {
				// noop
			}
		}

		const recognition = new SpeechRecognitionClass();
		recognition.lang = lang;
		recognition.interimResults = true;
		recognition.continuous = false;
		recognition.maxAlternatives = 1;

		recognition.onstart = () => {
			setError(null);
			setIsListening(true);
			setInterimTranscript("");
		};

		recognition.onresult = (event) => {
			let interim = "";
			let finalText = "";
			for (let i = event.resultIndex; i < event.results.length; i++) {
				const transcript = event.results[i][0].transcript;
				if (event.results[i].isFinal) {
					finalText += transcript;
				} else {
					interim += transcript;
				}
			}
			if (interim) setInterimTranscript(interim);
			if (finalText && onResultRef.current) {
				onResultRef.current(finalText.trim());
				setInterimTranscript("");
			}
		};

		recognition.onerror = (event) => {
			setError(event.error || "Ошибка распознавания");
			setIsListening(false);
		};

		recognition.onend = () => {
			setIsListening(false);
			setInterimTranscript("");
		};

		recognitionRef.current = recognition;
		try {
			recognition.start();
		} catch (e) {
			setError(e.message || "Не удалось запустить распознавание");
			setIsListening(false);
		}
	}, [lang]);

	useEffect(() => () => stop(), [stop]);

	return {
		isListening,
		error,
		interimTranscript,
		start,
		stop,
		supported: isSpeechRecognitionSupported(),
	};
}
