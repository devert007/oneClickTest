// Google Form API integration
const GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxFxkVPUicjMeHT-Qn2lIuSd-S9he7esbPoOOBj8-pK0biy7VgLQ-N8bLlLJI6xjKVt/exec"


export const googleFormAPI = {
	sendTestToGoogleForm: async (testJson) => {
		try {
			// Посылаем на backend прокси-эндпоинт (обходит CORS)
			const response = await fetch("http://localhost:8000/proxy-google-form", {
				method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          test: testJson,
          script_url: GOOGLE_SCRIPT_URL   // ← вот это было нужно!
        }),
			});
			// Проверяем статус ответа
			if (!response.ok) {
				const text = await response.text();
				throw new Error(
					`Google Apps Script ответ: ${response.status} ${response.statusText}. Тело: ${text}`,
				);
			}
			// Пробуем распарсить JSON
			let result = null;
			try {
				result = await response.json();
			} catch (e) {
				result = await response.text();
			}
      console.log(result)
			return result;
		} catch (error) {
			// Подробный вывод для диагностики
			if (
				error.name === "TypeError" &&
				error.message.includes("Failed to fetch")
			) {
				console.error(
					"❌ Failed to fetch: Проверьте URL скрипта, публикацию как веб-приложение, CORS и доступность из браузера.",
				);
				throw new Error(
					"Failed to fetch: Проверьте URL скрипта, публикацию как веб-приложение, CORS и доступность из браузера.",
				);
			}
			console.error("Ошибка отправки теста в Google Apps Script:", error);
			throw error;
		}
	},
};
