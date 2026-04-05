import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LoginForm } from "./LoginForm";

// Mock the auth context
const mockLogin = vi.fn();
const mockRegister = vi.fn();
const mockLogout = vi.fn();
const mockClearError = vi.fn();

let mockAuthState = {
	user: null as null | { id: string; username: string; email: string; created_at: string },
	loading: false,
	error: null as string | null,
	login: mockLogin,
	register: mockRegister,
	logout: mockLogout,
	clearError: mockClearError,
};

vi.mock("@/contexts/AuthContext", () => ({
	useAuth: () => mockAuthState,
	AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

beforeEach(() => {
	mockLogin.mockReset();
	mockRegister.mockReset();
	mockLogout.mockReset();
	mockClearError.mockReset();
	mockAuthState = {
		user: null,
		loading: false,
		error: null,
		login: mockLogin,
		register: mockRegister,
		logout: mockLogout,
		clearError: mockClearError,
	};
});

afterEach(() => {
	vi.restoreAllMocks();
});

describe("LoginForm", () => {
	it("renders login form by default", () => {
		render(<LoginForm />);
		expect(screen.getByTestId("form-title")).toHaveTextContent("ログイン");
		expect(screen.getByTestId("auth-username")).toBeDefined();
		expect(screen.getByTestId("auth-password")).toBeDefined();
		expect(screen.queryByTestId("auth-email")).toBeNull();
	});

	it("toggles to register form", async () => {
		const user = userEvent.setup();
		render(<LoginForm />);

		await user.click(screen.getByTestId("auth-toggle"));

		expect(screen.getByTestId("form-title")).toHaveTextContent("アカウント登録");
		expect(screen.getByTestId("auth-email")).toBeDefined();
	});

	it("toggles back to login form", async () => {
		const user = userEvent.setup();
		render(<LoginForm />);

		await user.click(screen.getByTestId("auth-toggle"));
		await user.click(screen.getByTestId("auth-toggle"));

		expect(screen.getByTestId("form-title")).toHaveTextContent("ログイン");
		expect(screen.queryByTestId("auth-email")).toBeNull();
	});

	it("calls login on form submit in login mode", async () => {
		const user = userEvent.setup();
		mockLogin.mockResolvedValue(undefined);

		render(<LoginForm />);

		await user.type(screen.getByTestId("auth-username"), "testuser");
		await user.type(screen.getByTestId("auth-password"), "password123");
		await user.click(screen.getByTestId("auth-submit"));

		await waitFor(() => {
			expect(mockLogin).toHaveBeenCalledWith("testuser", "password123");
		});
	});

	it("calls register on form submit in register mode", async () => {
		const user = userEvent.setup();
		mockRegister.mockResolvedValue(undefined);

		render(<LoginForm />);

		await user.click(screen.getByTestId("auth-toggle"));
		await user.type(screen.getByTestId("auth-username"), "newuser");
		await user.type(screen.getByTestId("auth-email"), "new@example.com");
		await user.type(screen.getByTestId("auth-password"), "password123");
		await user.click(screen.getByTestId("auth-submit"));

		await waitFor(() => {
			expect(mockRegister).toHaveBeenCalledWith("newuser", "new@example.com", "password123");
		});
	});

	it("displays error from auth context", () => {
		mockAuthState.error = "Invalid username or password";
		render(<LoginForm />);

		expect(screen.getByTestId("auth-error")).toHaveTextContent("Invalid username or password");
	});

	it("submit button is disabled when fields are empty", () => {
		render(<LoginForm />);

		const submitButton = screen.getByTestId("auth-submit");
		expect(submitButton).toBeDisabled();
	});

	it("clears error when toggling mode", async () => {
		const user = userEvent.setup();
		render(<LoginForm />);

		await user.click(screen.getByTestId("auth-toggle"));

		expect(mockClearError).toHaveBeenCalled();
	});
});
