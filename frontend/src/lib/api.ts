/**
 * API client for Memory Palace backend.
 */

import type {
	DailyStatsResponse,
	ForgettingCurveResponse,
	MemoryItem,
	MemoryItemCreateRequest,
	MemoryItemUpdateRequest,
	ReviewRecordCreate,
	ReviewRecordResponse,
	Room,
	RoomCreateRequest,
	RoomStatsResponse,
	RoomUpdateRequest,
} from "@/types/api";

const BASE_URL = "/api";

class ApiError extends Error {
	constructor(
		public readonly status: number,
		message: string,
	) {
		super(message);
		this.name = "ApiError";
	}
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
	const response = await fetch(`${BASE_URL}${path}`, {
		headers: {
			"Content-Type": "application/json",
			...options?.headers,
		},
		...options,
	});

	if (!response.ok) {
		const errorBody = await response.text().catch(() => "Unknown error");
		throw new ApiError(response.status, `API error ${response.status}: ${errorBody}`);
	}

	// 204 No Content
	if (response.status === 204) {
		return undefined as T;
	}

	return response.json() as Promise<T>;
}

// =============================================================================
// Room API
// =============================================================================

export const roomApi = {
	list(): Promise<Room[]> {
		return request<Room[]>("/rooms");
	},

	get(roomId: string): Promise<Room> {
		return request<Room>(`/rooms/${roomId}`);
	},

	create(data: RoomCreateRequest): Promise<Room> {
		return request<Room>("/rooms", {
			method: "POST",
			body: JSON.stringify(data),
		});
	},

	update(roomId: string, data: RoomUpdateRequest): Promise<Room> {
		return request<Room>(`/rooms/${roomId}`, {
			method: "PATCH",
			body: JSON.stringify(data),
		});
	},

	delete(roomId: string): Promise<void> {
		return request<void>(`/rooms/${roomId}`, {
			method: "DELETE",
		});
	},
};

// =============================================================================
// MemoryItem API
// =============================================================================

export const itemApi = {
	list(roomId: string): Promise<MemoryItem[]> {
		return request<MemoryItem[]>(`/rooms/${roomId}/items`);
	},

	get(roomId: string, itemId: string): Promise<MemoryItem> {
		return request<MemoryItem>(`/rooms/${roomId}/items/${itemId}`);
	},

	create(roomId: string, data: MemoryItemCreateRequest): Promise<MemoryItem> {
		return request<MemoryItem>(`/rooms/${roomId}/items`, {
			method: "POST",
			body: JSON.stringify(data),
		});
	},

	update(roomId: string, itemId: string, data: MemoryItemUpdateRequest): Promise<MemoryItem> {
		return request<MemoryItem>(`/rooms/${roomId}/items/${itemId}`, {
			method: "PATCH",
			body: JSON.stringify(data),
		});
	},

	delete(roomId: string, itemId: string): Promise<void> {
		return request<void>(`/rooms/${roomId}/items/${itemId}`, {
			method: "DELETE",
		});
	},
};

// =============================================================================
// Review API
// =============================================================================

export const reviewApi = {
	getQueue(roomId: string): Promise<MemoryItem[]> {
		return request<MemoryItem[]>(`/rooms/${roomId}/review-queue`);
	},

	recordReview(roomId: string, data: ReviewRecordCreate): Promise<ReviewRecordResponse> {
		return request<ReviewRecordResponse>(`/rooms/${roomId}/review`, {
			method: "POST",
			body: JSON.stringify(data),
		});
	},

	getStats(roomId: string): Promise<RoomStatsResponse> {
		return request<RoomStatsResponse>(`/rooms/${roomId}/stats`);
	},

	getDailyStats(roomId: string, days = 30): Promise<DailyStatsResponse> {
		return request<DailyStatsResponse>(`/rooms/${roomId}/stats/daily?days=${days}`);
	},

	getForgettingCurve(roomId: string): Promise<ForgettingCurveResponse> {
		return request<ForgettingCurveResponse>(`/rooms/${roomId}/stats/forgetting-curve`);
	},
};

export { ApiError };
