import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, TOKEN_KEY, useAuth } from "./AuthContext";

// Mock the API module
vi.mock("@/lib/api", () => ({
	authApi: {
		login: vi.fn(),
		register: vi.fn(),
		me: vi.fn(),
	},
	setOnUnauthorized: vi.fn(),
}));

const { authApi } = await import("@/lib/api");

// Test component that exposes auth state
function AuthConsumer(): React.JSX.Element {
	const { user, loading, error, login, register, logout, clearError } = useAuth();

	return (
		<div>
			<div data-testid="loading">{String(loading)}</div>
			<div data-testid="user">{user ? user.username : "null"}</div>
			<div data-testid="error">{error ?? "null"}</div>
			<button type="button" data-testid="login-btn" onClick={() => login("testuser", "pass123")}>
				Login
			</button>
			<button type="button" data-testid="register-btn" onClick={() => register("newuser", "a@b.com", "pass123")}>
				Register
			</button>
			<button type="button" data-testid="logout-btn" onClick={logout}>
				Logout
			</button>
			<button type="button" data-testid="clear-error-btn" onClick={clearError}>
				Clear Error
			</button>
		</div>
	);
}

beforeEach(() => {
	vi.mocked(authApi.login).mockReset();
	vi.mocked(authApi.register).mockReset();
	vi.mocked(authApi.me).mockReset();
	localStorage.clear();
});

afterEach(() => {
	vi.restoreAllMocks();
});

describe("AuthContext", () => {
	it("starts in loading state and resolves to unauthenticated when no token", async () => {
		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("loading")).toHaveTextContent("false");
			expect(screen.getByTestId("user")).toHaveTextContent("null");
		});
	});

	it("validates existing token on mount", async () => {
		localStorage.setItem(TOKEN_KEY, "valid-token");
		vi.mocked(authApi.me).mockResolvedValue({
			id: "user-1",
			username: "testuser",
			email: "test@example.com",
			created_at: "2026-01-01T00:00:00Z",
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("user")).toHaveTextContent("testuser");
		});
	});

	it("clears invalid token on mount", async () => {
		localStorage.setItem(TOKEN_KEY, "expired-token");
		vi.mocked(authApi.me).mockRejectedValue(new Error("Unauthorized"));

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("user")).toHaveTextContent("null");
			expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
		});
	});

	it("login stores token and fetches user", async () => {
		vi.mocked(authApi.login).mockResolvedValue({
			access_token: "new-token",
			token_type: "bearer",
		});
		vi.mocked(authApi.me).mockResolvedValue({
			id: "user-1",
			username: "testuser",
			email: "test@example.com",
			created_at: "2026-01-01T00:00:00Z",
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("loading")).toHaveTextContent("false");
		});

		await act(async () => {
			screen.getByTestId("login-btn").click();
		});

		await waitFor(() => {
			expect(screen.getByTestId("user")).toHaveTextContent("testuser");
			expect(localStorage.getItem(TOKEN_KEY)).toBe("new-token");
		});
	});

	it("register stores token and fetches user", async () => {
		vi.mocked(authApi.register).mockResolvedValue({
			access_token: "reg-token",
			token_type: "bearer",
		});
		vi.mocked(authApi.me).mockResolvedValue({
			id: "user-2",
			username: "newuser",
			email: "a@b.com",
			created_at: "2026-01-01T00:00:00Z",
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("loading")).toHaveTextContent("false");
		});

		await act(async () => {
			screen.getByTestId("register-btn").click();
		});

		await waitFor(() => {
			expect(screen.getByTestId("user")).toHaveTextContent("newuser");
			expect(localStorage.getItem(TOKEN_KEY)).toBe("reg-token");
		});
	});

	it("logout clears token and user", async () => {
		localStorage.setItem(TOKEN_KEY, "valid-token");
		vi.mocked(authApi.me).mockResolvedValue({
			id: "user-1",
			username: "testuser",
			email: "test@example.com",
			created_at: "2026-01-01T00:00:00Z",
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("user")).toHaveTextContent("testuser");
		});

		await act(async () => {
			screen.getByTestId("logout-btn").click();
		});

		expect(screen.getByTestId("user")).toHaveTextContent("null");
		expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
	});

	it("sets error on login failure", async () => {
		vi.mocked(authApi.login).mockRejectedValue(new Error("Invalid credentials"));

		// The login function re-throws, so the AuthConsumer button handler needs to catch it.
		// We use a custom consumer that catches the error from login.
		function LoginErrorConsumer(): React.JSX.Element {
			const { error, login } = useAuth();
			const handleClick = (): void => {
				login("testuser", "pass123").catch(() => {
					// Expected rejection — error is stored in context
				});
			};
			return (
				<div>
					<div data-testid="error">{error ?? "null"}</div>
					<button type="button" data-testid="login-btn" onClick={handleClick}>
						Login
					</button>
				</div>
			);
		}

		render(
			<AuthProvider>
				<LoginErrorConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("error")).toHaveTextContent("null");
		});

		await act(async () => {
			screen.getByTestId("login-btn").click();
		});

		await waitFor(() => {
			expect(screen.getByTestId("error")).toHaveTextContent("Invalid credentials");
		});
	});

	it("clearError resets error to null", async () => {
		vi.mocked(authApi.login).mockRejectedValue(new Error("Bad request"));

		// Custom consumer that catches login rejection
		function ClearErrorConsumer(): React.JSX.Element {
			const { error, login, clearError } = useAuth();
			const handleLogin = (): void => {
				login("testuser", "pass123").catch(() => {
					// Expected rejection
				});
			};
			return (
				<div>
					<div data-testid="error">{error ?? "null"}</div>
					<button type="button" data-testid="login-btn" onClick={handleLogin}>
						Login
					</button>
					<button type="button" data-testid="clear-error-btn" onClick={clearError}>
						Clear
					</button>
				</div>
			);
		}

		render(
			<AuthProvider>
				<ClearErrorConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("error")).toHaveTextContent("null");
		});

		await act(async () => {
			screen.getByTestId("login-btn").click();
		});

		await waitFor(() => {
			expect(screen.getByTestId("error")).not.toHaveTextContent("null");
		});

		await act(async () => {
			screen.getByTestId("clear-error-btn").click();
		});

		expect(screen.getByTestId("error")).toHaveTextContent("null");
	});

	it("throws error when useAuth is used outside AuthProvider", () => {
		// Suppress console.error for expected React error boundary noise
		const spy = vi.spyOn(console, "error").mockImplementation(() => {});

		expect(() => {
			render(<AuthConsumer />);
		}).toThrow("useAuth must be used within an AuthProvider");

		spy.mockRestore();
	});
});
