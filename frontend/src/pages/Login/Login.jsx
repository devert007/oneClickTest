import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { LogIn, Mail, Loader2 } from "lucide-react";
import "./Login.css";

const Login = () => {
	const [formData, setFormData] = useState({ email: "" });
	const [error, setError] = useState("");
	const [loading, setLoading] = useState(false);

	const { login } = useAuth();
	const navigate = useNavigate();

	const handleChange = (e) => {
		setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
	};

	const handleSubmit = async (e) => {
		e.preventDefault();
		setError("");
		setLoading(true);

		try {
			await login({ email: formData.email });
			navigate("/");
		} catch (err) {
			setError(err.message || "Ошибка входа. Проверьте email.");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="auth-page">
			<div className="auth-bg-shapes">
				<div className="auth-shape auth-shape-1" />
				<div className="auth-shape auth-shape-2" />
			</div>
			<div className="auth-card">
				<div className="auth-header">
					<div className="auth-logo">
						<LogIn size={28} />
					</div>
					<h1>OneClickTest</h1>
					<p>Войдите в аккаунт</p>
				</div>

				<form onSubmit={handleSubmit} className="auth-form">
					{error && <div className="auth-error">{error}</div>}

					<div className="auth-field">
						<label htmlFor="email">Email</label>
						<div className="auth-input-wrap">
							<Mail size={18} className="auth-input-icon" />
							<input
								type="email"
								id="email"
								name="email"
								value={formData.email}
								onChange={handleChange}
								required
								placeholder="Введите email"
							/>
						</div>
					</div>

					<button type="submit" disabled={loading} className="auth-submit-btn">
						{loading ? (
							<>
								<Loader2 size={18} className="spin" /> Вход...
							</>
						) : (
							"Войти"
						)}
					</button>
				</form>

				<div className="auth-footer">
					<p>
						Нет аккаунта? <Link to="/register">Зарегистрируйтесь</Link>
					</p>
				</div>
			</div>
		</div>
	);
};

export default Login;
