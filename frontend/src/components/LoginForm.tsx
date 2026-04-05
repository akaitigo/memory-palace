/**
 * Login / Register form component.
 * Toggles between login and registration mode.
 */

import { useCallback, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

type Mode = "login" | "register";

function isFormValid(mode: Mode, username: string, email: string, password: string): boolean {
	if (mode === "login") {
		return username.length > 0 && password.length > 0;
	}
	return username.length >= 3 && email.length > 0 && password.length >= 8;
}

export function LoginForm(): React.JSX.Element {
	const { login, register, error, clearError } = useAuth();
	const [mode, setMode] = useState<Mode>("login");
	const [username, setUsername] = useState("");
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [submitting, setSubmitting] = useState(false);

	const toggleMode = useCallback(() => {
		setMode((prev) => (prev === "login" ? "register" : "login"));
		clearError();
	}, [clearError]);

	const handleSubmit = useCallback(
		async (e: React.FormEvent) => {
			e.preventDefault();
			setSubmitting(true);
			try {
				if (mode === "login") {
					await login(username, password);
				} else {
					await register(username, email, password);
				}
			} catch {
				// Error is already stored in auth context
			} finally {
				setSubmitting(false);
			}
		},
		[mode, username, email, password, login, register],
	);

	const canSubmit = isFormValid(mode, username, email, password) && !submitting;

	return (
		<div style={styles.wrapper}>
			<div style={styles.card}>
				<h1 style={styles.title}>Memory Palace</h1>
				<p style={styles.subtitle}>記憶宮殿 - 間隔反復学習ツール</p>

				<h2 style={styles.formTitle} data-testid="form-title">
					{mode === "login" ? "ログイン" : "アカウント登録"}
				</h2>

				{error && (
					<p style={styles.error} data-testid="auth-error">
						{error}
					</p>
				)}

				<form onSubmit={handleSubmit} data-testid="auth-form">
					<div style={styles.field}>
						<label htmlFor="auth-username" style={styles.label}>
							ユーザー名
						</label>
						<input
							id="auth-username"
							type="text"
							value={username}
							onChange={(e) => setUsername(e.target.value)}
							placeholder={mode === "register" ? "3文字以上" : "ユーザー名"}
							autoComplete="username"
							style={styles.input}
							data-testid="auth-username"
						/>
					</div>

					{mode === "register" && (
						<div style={styles.field}>
							<label htmlFor="auth-email" style={styles.label}>
								メールアドレス
							</label>
							<input
								id="auth-email"
								type="email"
								value={email}
								onChange={(e) => setEmail(e.target.value)}
								placeholder="example@mail.com"
								autoComplete="email"
								style={styles.input}
								data-testid="auth-email"
							/>
						</div>
					)}

					<div style={styles.field}>
						<label htmlFor="auth-password" style={styles.label}>
							パスワード
						</label>
						<input
							id="auth-password"
							type="password"
							value={password}
							onChange={(e) => setPassword(e.target.value)}
							placeholder={mode === "register" ? "8文字以上" : "パスワード"}
							autoComplete={mode === "login" ? "current-password" : "new-password"}
							style={styles.input}
							data-testid="auth-password"
						/>
					</div>

					<button
						type="submit"
						disabled={!canSubmit}
						style={{
							...styles.submitButton,
							...(!canSubmit ? styles.submitDisabled : {}),
						}}
						data-testid="auth-submit"
					>
						{submitting ? "処理中..." : mode === "login" ? "ログイン" : "登録"}
					</button>
				</form>

				<button type="button" onClick={toggleMode} style={styles.toggleButton} data-testid="auth-toggle">
					{mode === "login" ? "アカウントをお持ちでない方はこちら" : "既にアカウントをお持ちの方はこちら"}
				</button>
			</div>
		</div>
	);
}

// =============================================================================
// Inline styles
// =============================================================================

const styles = {
	wrapper: {
		minHeight: "100vh",
		display: "flex",
		alignItems: "center",
		justifyContent: "center",
		backgroundColor: "#0a0a1a",
		fontFamily: "system-ui, sans-serif",
		padding: "20px",
	},
	card: {
		width: "100%",
		maxWidth: "400px",
		padding: "40px 32px",
		backgroundColor: "#1a1a2e",
		borderRadius: "12px",
		border: "1px solid #2a2a4a",
	},
	title: {
		margin: "0 0 4px",
		fontSize: "1.8rem",
		color: "#e0e0e0",
		textAlign: "center" as const,
	},
	subtitle: {
		margin: "0 0 32px",
		fontSize: "0.9rem",
		color: "#888",
		textAlign: "center" as const,
	},
	formTitle: {
		margin: "0 0 16px",
		fontSize: "1.2rem",
		color: "#e0e0e0",
		textAlign: "center" as const,
	},
	error: {
		color: "#ff4444",
		fontSize: "0.85rem",
		marginBottom: "12px",
		padding: "8px 12px",
		backgroundColor: "rgba(255, 68, 68, 0.1)",
		borderRadius: "6px",
		border: "1px solid rgba(255, 68, 68, 0.3)",
	},
	field: {
		marginBottom: "16px",
	},
	label: {
		display: "block",
		marginBottom: "6px",
		fontSize: "0.85rem",
		color: "#aaa",
	},
	input: {
		width: "100%",
		padding: "10px 14px",
		backgroundColor: "#2a2a4a",
		border: "1px solid #3a3a5c",
		borderRadius: "8px",
		color: "#e0e0e0",
		fontSize: "0.95rem",
		outline: "none",
		boxSizing: "border-box" as const,
	},
	submitButton: {
		width: "100%",
		padding: "12px",
		backgroundColor: "#0066cc",
		color: "#fff",
		border: "none",
		borderRadius: "8px",
		cursor: "pointer",
		fontSize: "1rem",
		fontWeight: 600,
		marginTop: "8px",
	},
	submitDisabled: {
		backgroundColor: "#333",
		color: "#666",
		cursor: "not-allowed",
	},
	toggleButton: {
		display: "block",
		width: "100%",
		marginTop: "16px",
		padding: "8px",
		background: "none",
		border: "none",
		color: "#4488ff",
		cursor: "pointer",
		fontSize: "0.85rem",
		textAlign: "center" as const,
	},
} satisfies Record<string, React.CSSProperties>;
