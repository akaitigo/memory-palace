import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StatsDashboard } from "./StatsDashboard";

// Mock recharts to avoid canvas/SVG issues in tests
vi.mock("recharts", () => ({
	ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
		<div data-testid="responsive-container">{children}</div>
	),
	LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
	PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
	Line: () => <div data-testid="line" />,
	Pie: () => <div data-testid="pie" />,
	Cell: () => <div data-testid="cell" />,
	XAxis: () => <div />,
	YAxis: () => <div />,
	CartesianGrid: () => <div />,
	Tooltip: () => <div />,
	Legend: () => <div />,
}));

// Mock the API module
vi.mock("@/lib/api", () => ({
	reviewApi: {
		getStats: vi.fn(),
		getDailyStats: vi.fn(),
		getForgettingCurve: vi.fn(),
	},
}));

const { reviewApi } = await import("@/lib/api");

const mockOnBack = vi.fn();

const MOCK_STATS = {
	total_items: 10,
	reviewed_items: 7,
	mastered_items: 3,
	learning_items: 4,
	new_items: 3,
	average_ease_factor: 2.6,
	total_reviews: 25,
	average_quality: 3.8,
	reviews_today: 5,
};

const MOCK_DAILY = {
	entries: [
		{ date: "2026-03-28", review_count: 3, average_quality: 4.0, correct_rate: 100.0 },
		{ date: "2026-03-29", review_count: 5, average_quality: 3.5, correct_rate: 80.0 },
	],
};

const MOCK_CURVES = {
	items: [
		{
			item_id: "item-1",
			content: "Test item",
			stability: 2.5,
			curve: [
				{ days_since_review: 0, retention: 1.0 },
				{ days_since_review: 1, retention: 0.67 },
				{ days_since_review: 2, retention: 0.45 },
			],
		},
	],
};

beforeEach(() => {
	vi.mocked(reviewApi.getStats).mockResolvedValue(MOCK_STATS);
	vi.mocked(reviewApi.getDailyStats).mockResolvedValue(MOCK_DAILY);
	vi.mocked(reviewApi.getForgettingCurve).mockResolvedValue(MOCK_CURVES);
	mockOnBack.mockReset();
});

afterEach(() => {
	vi.restoreAllMocks();
});

describe("StatsDashboard", () => {
	it("shows loading state initially", () => {
		vi.mocked(reviewApi.getStats).mockReturnValue(new Promise(() => {}));
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);
		expect(screen.getByTestId("stats-loading")).toBeDefined();
	});

	it("renders summary cards after loading", async () => {
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("stats-summary")).toBeDefined();
			expect(screen.getByText("10")).toBeDefined();
			expect(screen.getByText("25")).toBeDefined();
			expect(screen.getByText("5")).toBeDefined();
			expect(screen.getByText("3.8")).toBeDefined();
		});
	});

	it("renders mastery chart", async () => {
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("mastery-chart")).toBeDefined();
		});
	});

	it("renders daily chart", async () => {
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("daily-chart")).toBeDefined();
		});
	});

	it("renders forgetting curve chart", async () => {
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("forgetting-curve-chart")).toBeDefined();
		});
	});

	it("calls onBack when back button is clicked", async () => {
		const user = userEvent.setup();
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("stats-back-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("stats-back-button"));
		expect(mockOnBack).toHaveBeenCalledOnce();
	});

	it("shows date range buttons", async () => {
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("range-7")).toBeDefined();
			expect(screen.getByTestId("range-14")).toBeDefined();
			expect(screen.getByTestId("range-30")).toBeDefined();
			expect(screen.getByTestId("range-90")).toBeDefined();
		});
	});

	it("reloads data when date range changes", async () => {
		const user = userEvent.setup();
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("range-7")).toBeDefined();
		});

		await user.click(screen.getByTestId("range-7"));

		await waitFor(() => {
			expect(reviewApi.getDailyStats).toHaveBeenCalledWith("room-1", 7);
		});
	});

	it("shows error state on API failure", async () => {
		vi.mocked(reviewApi.getStats).mockRejectedValue(new Error("Network error"));
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("stats-error")).toBeDefined();
		});
	});

	it("hides mastery chart when no items", async () => {
		vi.mocked(reviewApi.getStats).mockResolvedValue({
			...MOCK_STATS,
			total_items: 0,
			mastered_items: 0,
			learning_items: 0,
			new_items: 0,
		});
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("stats-dashboard")).toBeDefined();
		});

		expect(screen.queryByTestId("mastery-chart")).toBeNull();
	});

	it("hides forgetting curve chart when no reviewed items", async () => {
		vi.mocked(reviewApi.getForgettingCurve).mockResolvedValue({ items: [] });
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("stats-dashboard")).toBeDefined();
		});

		expect(screen.queryByTestId("forgetting-curve-chart")).toBeNull();
	});

	it("shows mobile warning", async () => {
		render(<StatsDashboard roomId="room-1" onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("mobile-warning")).toBeDefined();
		});
	});
});
