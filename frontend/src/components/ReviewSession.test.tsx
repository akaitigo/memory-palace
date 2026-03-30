import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReviewSession } from "./ReviewSession";

// Mock the API module
vi.mock("@/lib/api", () => ({
	reviewApi: {
		getQueue: vi.fn(),
		recordReview: vi.fn(),
	},
}));

const { reviewApi } = await import("@/lib/api");

const mockOnComplete = vi.fn();
const mockOnBack = vi.fn();

const MOCK_ITEM_1 = {
	id: "item-1",
	room_id: "room-1",
	content: "The capital of Japan is Tokyo",
	image_url: null,
	position_x: 1.0,
	position_y: 0,
	position_z: 2.0,
	ease_factor: 2.5,
	interval: 1,
	repetitions: 0,
	last_reviewed_at: null,
	created_at: "2026-01-01T00:00:00Z",
	updated_at: "2026-01-01T00:00:00Z",
};

const MOCK_ITEM_2 = {
	id: "item-2",
	room_id: "room-1",
	content: "Water boils at 100 degrees Celsius",
	image_url: null,
	position_x: 3.0,
	position_y: 0,
	position_z: -1.0,
	ease_factor: 2.5,
	interval: 1,
	repetitions: 0,
	last_reviewed_at: null,
	created_at: "2026-01-01T00:00:00Z",
	updated_at: "2026-01-01T00:00:00Z",
};

const MOCK_ITEMS = [MOCK_ITEM_1, MOCK_ITEM_2];

beforeEach(() => {
	vi.mocked(reviewApi.getQueue).mockResolvedValue([]);
	vi.mocked(reviewApi.recordReview).mockResolvedValue({
		id: "review-1",
		session_id: "session-1",
		memory_item_id: "item-1",
		quality: 5,
		response_time_ms: 1000,
		reviewed_at: "2026-01-01T00:00:00Z",
	});
	mockOnComplete.mockReset();
	mockOnBack.mockReset();
});

afterEach(() => {
	vi.restoreAllMocks();
});

describe("ReviewSession", () => {
	it("shows loading state initially", () => {
		vi.mocked(reviewApi.getQueue).mockReturnValue(new Promise(() => {}));
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);
		expect(screen.getByTestId("review-loading")).toBeDefined();
	});

	it("shows empty state when no items to review", async () => {
		vi.mocked(reviewApi.getQueue).mockResolvedValue([]);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("review-empty")).toBeDefined();
			expect(screen.getByText("復習するアイテムがありません")).toBeDefined();
		});
	});

	it("shows review card when items are available", async () => {
		vi.mocked(reviewApi.getQueue).mockResolvedValue(MOCK_ITEMS);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("review-active")).toBeDefined();
			expect(screen.getByTestId("review-card")).toBeDefined();
			expect(screen.getByText("1 / 2")).toBeDefined();
		});
	});

	it("shows content when show button is clicked", async () => {
		const user = userEvent.setup();
		vi.mocked(reviewApi.getQueue).mockResolvedValue(MOCK_ITEMS);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("show-content-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("show-content-button"));

		await waitFor(() => {
			expect(screen.getByTestId("revealed-content")).toBeDefined();
			expect(screen.getByText("The capital of Japan is Tokyo")).toBeDefined();
		});
	});

	it("shows quality buttons after revealing content", async () => {
		const user = userEvent.setup();
		vi.mocked(reviewApi.getQueue).mockResolvedValue(MOCK_ITEMS);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("show-content-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("show-content-button"));

		await waitFor(() => {
			for (let q = 0; q <= 5; q++) {
				expect(screen.getByTestId(`quality-button-${q}`)).toBeDefined();
			}
		});
	});

	it("records review and advances to next item", async () => {
		const user = userEvent.setup();
		vi.mocked(reviewApi.getQueue).mockResolvedValue(MOCK_ITEMS);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("show-content-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("show-content-button"));
		await user.click(screen.getByTestId("quality-button-5"));

		await waitFor(() => {
			expect(reviewApi.recordReview).toHaveBeenCalledWith("room-1", {
				memory_item_id: "item-1",
				quality: 5,
				response_time_ms: expect.any(Number),
			});
			// Should show next item (2/2)
			expect(screen.getByText("2 / 2")).toBeDefined();
		});
	});

	it("shows completion screen after all items reviewed", async () => {
		const user = userEvent.setup();
		vi.mocked(reviewApi.getQueue).mockResolvedValue([MOCK_ITEM_1]);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("show-content-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("show-content-button"));
		await user.click(screen.getByTestId("quality-button-4"));

		await waitFor(() => {
			expect(screen.getByTestId("review-complete")).toBeDefined();
			expect(screen.getByText("復習完了")).toBeDefined();
		});
	});

	it("calls onBack when back button is clicked in empty state", async () => {
		const user = userEvent.setup();
		vi.mocked(reviewApi.getQueue).mockResolvedValue([]);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("review-back-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("review-back-button"));
		expect(mockOnBack).toHaveBeenCalledOnce();
	});

	it("calls onComplete when view stats button is clicked", async () => {
		const user = userEvent.setup();
		vi.mocked(reviewApi.getQueue).mockResolvedValue([MOCK_ITEM_1]);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("show-content-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("show-content-button"));
		await user.click(screen.getByTestId("quality-button-5"));

		await waitFor(() => {
			expect(screen.getByTestId("view-stats-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("view-stats-button"));
		expect(mockOnComplete).toHaveBeenCalledOnce();
	});

	it("shows error state on API failure", async () => {
		vi.mocked(reviewApi.getQueue).mockRejectedValue(new Error("Network error"));
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("review-error")).toBeDefined();
		});
	});

	it("shows correct rate in completion screen", async () => {
		const user = userEvent.setup();
		vi.mocked(reviewApi.getQueue).mockResolvedValue([MOCK_ITEM_1]);
		render(<ReviewSession roomId="room-1" onComplete={mockOnComplete} onBack={mockOnBack} />);

		await waitFor(() => {
			expect(screen.getByTestId("show-content-button")).toBeDefined();
		});

		await user.click(screen.getByTestId("show-content-button"));
		await user.click(screen.getByTestId("quality-button-5"));

		await waitFor(() => {
			expect(screen.getByText("100%")).toBeDefined();
			expect(screen.getByText("1/1")).toBeDefined();
		});
	});
});
