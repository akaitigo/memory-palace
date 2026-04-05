import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, authApi, itemApi, reviewApi, roomApi, setOnUnauthorized } from "./api";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function mockResponse(body: unknown, status = 200): Response {
	return {
		ok: status >= 200 && status < 300,
		status,
		json: () => Promise.resolve(body),
		text: () => Promise.resolve(JSON.stringify(body)),
		headers: new Headers(),
		redirected: false,
		statusText: "OK",
		type: "basic" as ResponseType,
		url: "",
		clone: () => mockResponse(body, status),
		body: null,
		bodyUsed: false,
		arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
		blob: () => Promise.resolve(new Blob()),
		formData: () => Promise.resolve(new FormData()),
		bytes: () => Promise.resolve(new Uint8Array()),
	};
}

function mockNoContentResponse(): Response {
	return mockResponse(undefined, 204);
}

function mockErrorResponse(status: number, message: string): Response {
	return {
		...mockResponse(message, status),
		ok: false,
		status,
		text: () => Promise.resolve(message),
	};
}

beforeEach(() => {
	mockFetch.mockReset();
	localStorage.clear();
	setOnUnauthorized(null);
});

afterEach(() => {
	vi.restoreAllMocks();
});

describe("roomApi", () => {
	describe("list", () => {
		it("fetches rooms from /api/rooms", async () => {
			const rooms = [{ id: "1", name: "Room 1" }];
			mockFetch.mockResolvedValueOnce(mockResponse(rooms));

			const result = await roomApi.list();

			expect(mockFetch).toHaveBeenCalledWith(
				"/api/rooms",
				expect.objectContaining({ headers: expect.objectContaining({ "Content-Type": "application/json" }) }),
			);
			expect(result).toEqual(rooms);
		});
	});

	describe("get", () => {
		it("fetches a room by ID", async () => {
			const room = { id: "1", name: "Test Room" };
			mockFetch.mockResolvedValueOnce(mockResponse(room));

			const result = await roomApi.get("1");
			expect(result).toEqual(room);
		});
	});

	describe("create", () => {
		it("creates a room with POST", async () => {
			const newRoom = { id: "1", name: "New Room" };
			mockFetch.mockResolvedValueOnce(mockResponse(newRoom, 201));

			const result = await roomApi.create({ name: "New Room" });

			expect(mockFetch).toHaveBeenCalledWith(
				"/api/rooms",
				expect.objectContaining({
					method: "POST",
					body: JSON.stringify({ name: "New Room" }),
				}),
			);
			expect(result).toEqual(newRoom);
		});
	});

	describe("update", () => {
		it("updates a room with PATCH", async () => {
			const updated = { id: "1", name: "Updated" };
			mockFetch.mockResolvedValueOnce(mockResponse(updated));

			const result = await roomApi.update("1", { name: "Updated" });
			expect(result).toEqual(updated);
		});
	});

	describe("delete", () => {
		it("deletes a room", async () => {
			mockFetch.mockResolvedValueOnce(mockNoContentResponse());

			await roomApi.delete("1");

			expect(mockFetch).toHaveBeenCalledWith("/api/rooms/1", expect.objectContaining({ method: "DELETE" }));
		});
	});
});

describe("itemApi", () => {
	const roomId = "room-1";

	describe("list", () => {
		it("fetches items for a room", async () => {
			const items = [{ id: "i1", content: "Test" }];
			mockFetch.mockResolvedValueOnce(mockResponse(items));

			const result = await itemApi.list(roomId);
			expect(result).toEqual(items);
		});
	});

	describe("create", () => {
		it("creates an item with position", async () => {
			const newItem = { id: "i1", content: "New item", position_x: 1, position_z: 2 };
			mockFetch.mockResolvedValueOnce(mockResponse(newItem, 201));

			const result = await itemApi.create(roomId, {
				content: "New item",
				position: { x: 1, y: 0, z: 2 },
			});

			expect(result).toEqual(newItem);
			expect(mockFetch).toHaveBeenCalledWith(
				`/api/rooms/${roomId}/items`,
				expect.objectContaining({
					method: "POST",
					body: expect.stringContaining("New item"),
				}),
			);
		});
	});

	describe("update", () => {
		it("updates an item", async () => {
			const updated = { id: "i1", content: "Updated" };
			mockFetch.mockResolvedValueOnce(mockResponse(updated));

			const result = await itemApi.update(roomId, "i1", { content: "Updated" });
			expect(result).toEqual(updated);
		});
	});

	describe("delete", () => {
		it("deletes an item", async () => {
			mockFetch.mockResolvedValueOnce(mockNoContentResponse());

			await itemApi.delete(roomId, "i1");

			expect(mockFetch).toHaveBeenCalledWith(
				`/api/rooms/${roomId}/items/i1`,
				expect.objectContaining({ method: "DELETE" }),
			);
		});
	});
});

describe("reviewApi", () => {
	const roomId = "room-1";

	describe("getQueue", () => {
		it("fetches review queue for a room", async () => {
			const queue = [{ id: "i1", content: "Test" }];
			mockFetch.mockResolvedValueOnce(mockResponse(queue));

			const result = await reviewApi.getQueue(roomId);
			expect(result).toEqual(queue);
			expect(mockFetch).toHaveBeenCalledWith(
				`/api/rooms/${roomId}/review-queue`,
				expect.objectContaining({ headers: expect.objectContaining({ "Content-Type": "application/json" }) }),
			);
		});
	});

	describe("recordReview", () => {
		it("posts a review result", async () => {
			const reviewResult = { id: "r1", quality: 5 };
			mockFetch.mockResolvedValueOnce(mockResponse(reviewResult, 201));

			const result = await reviewApi.recordReview(roomId, {
				memory_item_id: "item-1",
				quality: 5,
				response_time_ms: 1000,
			});

			expect(result).toEqual(reviewResult);
			expect(mockFetch).toHaveBeenCalledWith(
				`/api/rooms/${roomId}/review`,
				expect.objectContaining({
					method: "POST",
					body: expect.stringContaining("item-1"),
				}),
			);
		});
	});

	describe("getStats", () => {
		it("fetches room stats", async () => {
			const stats = { total_items: 10, total_reviews: 25 };
			mockFetch.mockResolvedValueOnce(mockResponse(stats));

			const result = await reviewApi.getStats(roomId);
			expect(result).toEqual(stats);
		});
	});

	describe("getDailyStats", () => {
		it("fetches daily stats with days parameter", async () => {
			const daily = { entries: [] };
			mockFetch.mockResolvedValueOnce(mockResponse(daily));

			const result = await reviewApi.getDailyStats(roomId, 7);
			expect(result).toEqual(daily);
			expect(mockFetch).toHaveBeenCalledWith(
				`/api/rooms/${roomId}/stats/daily?days=7`,
				expect.objectContaining({ headers: expect.objectContaining({ "Content-Type": "application/json" }) }),
			);
		});

		it("uses default 30 days", async () => {
			const daily = { entries: [] };
			mockFetch.mockResolvedValueOnce(mockResponse(daily));

			await reviewApi.getDailyStats(roomId);
			expect(mockFetch).toHaveBeenCalledWith(`/api/rooms/${roomId}/stats/daily?days=30`, expect.objectContaining({}));
		});
	});

	describe("getForgettingCurve", () => {
		it("fetches forgetting curve data", async () => {
			const curves = { items: [] };
			mockFetch.mockResolvedValueOnce(mockResponse(curves));

			const result = await reviewApi.getForgettingCurve(roomId);
			expect(result).toEqual(curves);
		});
	});
});

describe("ApiError", () => {
	it("is thrown on non-OK responses", async () => {
		mockFetch.mockResolvedValueOnce(mockErrorResponse(404, "Not found"));

		await expect(roomApi.get("nonexistent")).rejects.toThrow(ApiError);
	});

	it("includes status code and message", async () => {
		mockFetch.mockResolvedValueOnce(mockErrorResponse(500, "Internal error"));

		try {
			await roomApi.get("err");
			expect.unreachable("Should have thrown");
		} catch (err) {
			expect(err).toBeInstanceOf(ApiError);
			if (err instanceof ApiError) {
				expect(err.status).toBe(500);
				expect(err.message).toContain("Internal error");
			}
		}
	});
});

describe("authApi", () => {
	describe("register", () => {
		it("posts registration data", async () => {
			const tokenResp = { access_token: "tok", token_type: "bearer" };
			mockFetch.mockResolvedValueOnce(mockResponse(tokenResp, 201));

			const result = await authApi.register({
				username: "newuser",
				email: "new@test.com",
				password: "password123",
			});

			expect(result).toEqual(tokenResp);
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/auth/register",
				expect.objectContaining({
					method: "POST",
					body: expect.stringContaining("newuser"),
				}),
			);
		});
	});

	describe("login", () => {
		it("posts login credentials", async () => {
			const tokenResp = { access_token: "tok", token_type: "bearer" };
			mockFetch.mockResolvedValueOnce(mockResponse(tokenResp));

			const result = await authApi.login({
				username: "testuser",
				password: "password123",
			});

			expect(result).toEqual(tokenResp);
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/auth/login",
				expect.objectContaining({
					method: "POST",
					body: expect.stringContaining("testuser"),
				}),
			);
		});
	});

	describe("me", () => {
		it("fetches current user", async () => {
			const user = { id: "1", username: "testuser", email: "test@test.com", created_at: "2026-01-01" };
			mockFetch.mockResolvedValueOnce(mockResponse(user));

			const result = await authApi.me();
			expect(result).toEqual(user);
		});
	});
});

describe("Authorization header", () => {
	it("sends Bearer token when token exists in localStorage", async () => {
		localStorage.setItem("memory_palace_token", "my-jwt-token");
		mockFetch.mockResolvedValueOnce(mockResponse([]));

		await roomApi.list();

		expect(mockFetch).toHaveBeenCalledWith(
			"/api/rooms",
			expect.objectContaining({
				headers: expect.objectContaining({
					Authorization: "Bearer my-jwt-token",
				}),
			}),
		);
	});

	it("does not send Authorization header when no token", async () => {
		mockFetch.mockResolvedValueOnce(mockResponse([]));

		await roomApi.list();

		const callHeaders = mockFetch.mock.calls[0]?.[1]?.headers;
		expect(callHeaders).not.toHaveProperty("Authorization");
	});
});

describe("401 handler", () => {
	it("calls onUnauthorized callback on 401 response", async () => {
		const handler = vi.fn();
		setOnUnauthorized(handler);

		mockFetch.mockResolvedValueOnce(mockErrorResponse(401, "Unauthorized"));

		await expect(roomApi.list()).rejects.toThrow(ApiError);
		expect(handler).toHaveBeenCalledOnce();
	});

	it("does not call onUnauthorized on other errors", async () => {
		const handler = vi.fn();
		setOnUnauthorized(handler);

		mockFetch.mockResolvedValueOnce(mockErrorResponse(500, "Server error"));

		await expect(roomApi.list()).rejects.toThrow(ApiError);
		expect(handler).not.toHaveBeenCalled();
	});
});
