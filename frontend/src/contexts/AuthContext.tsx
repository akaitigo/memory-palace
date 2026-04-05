/**
 * Authentication context — manages JWT token state and provides
 * login/register/logout actions to the component tree.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "@/lib/api";
import type { UserResponse } from "@/types/api";

const TOKEN_KEY = "memory_palace_token";

interface AuthState {
	/** The authenticated user, or null when not logged in. */
	user: UserResponse | null;
	/** True while the initial token validation is in progress. */
	loading: boolean;
	/** The most recent authentication error message. */
	error: string | null;
}

interface AuthActions {
	login: (username: string, password: string) => Promise<void>;
	register: (username: string, email: string, password: string) => Promise<void>;
	logout: () => void;
	clearError: () => void;
}

type AuthContextValue = AuthState & AuthActions;

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

function getStoredToken(): string | null {
	try {
		return localStorage.getItem(TOKEN_KEY);
	} catch {
		return null;
	}
}

function storeToken(token: string): void {
	try {
		localStorage.setItem(TOKEN_KEY, token);
	} catch {
		// localStorage unavailable (e.g. private browsing quota exceeded)
	}
}

function clearToken(): void {
	try {
		localStorage.removeItem(TOKEN_KEY);
	} catch {
		// noop
	}
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
	const [state, setState] = useState<AuthState>({
		user: null,
		loading: true,
		error: null,
	});

	// On mount, attempt to validate an existing token
	useEffect(() => {
		const token = getStoredToken();
		if (!token) {
			setState({ user: null, loading: false, error: null });
			return;
		}

		let cancelled = false;
		authApi
			.me()
			.then((user) => {
				if (!cancelled) {
					setState({ user, loading: false, error: null });
				}
			})
			.catch(() => {
				// Token is invalid / expired — clear it
				clearToken();
				if (!cancelled) {
					setState({ user: null, loading: false, error: null });
				}
			});

		return () => {
			cancelled = true;
		};
	}, []);

	const login = useCallback(async (username: string, password: string): Promise<void> => {
		setState((prev) => ({ ...prev, error: null }));
		try {
			const tokenResp = await authApi.login({ username, password });
			storeToken(tokenResp.access_token);
			const user = await authApi.me();
			setState({ user, loading: false, error: null });
		} catch (err) {
			const message = err instanceof Error ? err.message : "Login failed";
			setState((prev) => ({ ...prev, error: message }));
			throw err;
		}
	}, []);

	const register = useCallback(async (username: string, email: string, password: string): Promise<void> => {
		setState((prev) => ({ ...prev, error: null }));
		try {
			const tokenResp = await authApi.register({ username, email, password });
			storeToken(tokenResp.access_token);
			const user = await authApi.me();
			setState({ user, loading: false, error: null });
		} catch (err) {
			const message = err instanceof Error ? err.message : "Registration failed";
			setState((prev) => ({ ...prev, error: message }));
			throw err;
		}
	}, []);

	const logout = useCallback(() => {
		clearToken();
		setState({ user: null, loading: false, error: null });
	}, []);

	const clearError = useCallback(() => {
		setState((prev) => ({ ...prev, error: null }));
	}, []);

	const value = useMemo<AuthContextValue>(
		() => ({
			...state,
			login,
			register,
			logout,
			clearError,
		}),
		[state, login, register, logout, clearError],
	);

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
	const ctx = useContext(AuthContext);
	if (ctx === null) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return ctx;
}

export { TOKEN_KEY };
