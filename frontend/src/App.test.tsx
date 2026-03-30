import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

// Mock the API module
vi.mock("@/lib/api", () => ({
	roomApi: {
		list: vi.fn(),
		create: vi.fn(),
		delete: vi.fn(),
	},
	itemApi: {
		list: vi.fn(),
	},
	reviewApi: {
		getQueue: vi.fn(),
		recordReview: vi.fn(),
		getStats: vi.fn(),
		getDailyStats: vi.fn(),
		getForgettingCurve: vi.fn(),
	},
}));

// Mock recharts
vi.mock("recharts", () => ({
	ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
	LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
	PieChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
	Line: () => <div />,
	Pie: () => <div />,
	Cell: () => <div />,
	XAxis: () => <div />,
	YAxis: () => <div />,
	CartesianGrid: () => <div />,
	Tooltip: () => <div />,
	Legend: () => <div />,
}));

// Import mocked module
const { roomApi } = await import("@/lib/api");

beforeEach(() => {
	vi.mocked(roomApi.list).mockResolvedValue([]);
});

afterEach(() => {
	vi.restoreAllMocks();
});

describe("App", () => {
	it("renders the heading", async () => {
		render(<App />);
		expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Memory Palace");
	});

	it("renders the description text", async () => {
		render(<App />);
		expect(screen.getByText("記憶宮殿 - 間隔反復学習ツール")).toBeDefined();
	});

	it("shows empty state when no rooms exist", async () => {
		vi.mocked(roomApi.list).mockResolvedValue([]);
		render(<App />);

		await waitFor(() => {
			expect(screen.getByTestId("no-rooms-message")).toBeDefined();
		});
	});

	it("displays rooms from the API", async () => {
		vi.mocked(roomApi.list).mockResolvedValue([
			{
				id: "room-1",
				owner_id: "owner-1",
				name: "My Room",
				description: null,
				layout_data: null,
				created_at: "2026-01-01T00:00:00Z",
				updated_at: "2026-01-01T00:00:00Z",
			},
		]);
		render(<App />);

		await waitFor(() => {
			expect(screen.getByTestId("room-list")).toBeDefined();
			expect(screen.getByText("My Room")).toBeDefined();
		});
	});

	it("has a room name input and create button", async () => {
		render(<App />);

		await waitFor(() => {
			expect(screen.getByTestId("room-name-input")).toBeDefined();
			expect(screen.getByTestId("create-room-button")).toBeDefined();
		});
	});

	it("create button is disabled when input is empty", async () => {
		render(<App />);

		await waitFor(() => {
			const button = screen.getByTestId("create-room-button");
			expect(button).toBeDisabled();
		});
	});

	it("creates a room when form is submitted", async () => {
		const user = userEvent.setup();
		vi.mocked(roomApi.create).mockResolvedValue({
			id: "new-room",
			owner_id: "owner-1",
			name: "New Room",
			description: null,
			layout_data: null,
			created_at: "2026-01-01T00:00:00Z",
			updated_at: "2026-01-01T00:00:00Z",
		});

		render(<App />);

		await waitFor(() => {
			expect(screen.getByTestId("room-name-input")).toBeDefined();
		});

		const input = screen.getByTestId("room-name-input");
		const button = screen.getByTestId("create-room-button");

		await user.type(input, "New Room");
		await user.click(button);

		await waitFor(() => {
			expect(roomApi.create).toHaveBeenCalledWith({ name: "New Room" });
			expect(screen.getByText("New Room")).toBeDefined();
		});
	});

	it("shows error message on API failure", async () => {
		vi.mocked(roomApi.list).mockRejectedValue(new Error("Network error"));
		render(<App />);

		await waitFor(() => {
			expect(screen.getByTestId("error-message")).toBeDefined();
		});
	});
});
