/**
 * API client for Memory Palace backend.
 */

import type {
	DailyStatsResponse,
	ForgettingCurveResponse,
	LoginRequest,
	MemoryItem,
	MemoryItemCreateRequest,
	MemoryItemUpdateRequest,
	RegisterRequest,
	ReviewRecordCreate,
	ReviewRecordResponse,
	Room,
	RoomCreateRequest,
	RoomStatsResponse,
	RoomUpdateRequest,
	TokenResponse,
	UserResponse,
} from "@/types/api";

const BASE_URL = "/api";
const TOKEN_KEY = "memory_palace_token";

/** Callback invoked when a 401 response is received (token expired / invalid). */
let onUnauthorized: (() => void) | null = null;

/**
 * Register a global handler that is called on 401 responses.
 * Used by AuthProvider to trigger logout + redirect to login screen.
 */
export function setOnUnauthorized(handler: (() => void) | null): void {
	onUnauthorized = handler;
}

class ApiError extends Error {
	constructor(
		public readonly status: number,
		message: string,
	) {
		super(message);
		this.name = "ApiError";
	}
}

function getToken(): string | null {
	try {
		return localStorage.getItem(TOKEN_KEY);
	} catch {
		return null;
	}
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
	const token = getToken();
	const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

	const response = await fetch(`${BASE_URL}${path}`, {
		headers: {
			"Content-Type": "application/json",
			...authHeaders,
			...options?.headers,
		},
		...options,
	});

	if (!response.ok) {
		if (response.status === 401) {
			onUnauthorized?.();
		}
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
		const params = new URLSearchParams({ days: String(days) });
		return request<DailyStatsResponse>(`/rooms/${roomId}/stats/daily?${params.toString()}`);
	},

	getForgettingCurve(roomId: string): Promise<ForgettingCurveResponse> {
		return request<ForgettingCurveResponse>(`/rooms/${roomId}/stats/forgetting-curve`);
	},
};

// =============================================================================
// Auth API
// =============================================================================

export const authApi = {
	register(data: RegisterRequest): Promise<TokenResponse> {
		return request<TokenResponse>("/auth/register", {
			method: "POST",
			body: JSON.stringify(data),
		});
	},

	login(data: LoginRequest): Promise<TokenResponse> {
		return request<TokenResponse>("/auth/login", {
			method: "POST",
			body: JSON.stringify(data),
		});
	},

	me(): Promise<UserResponse> {
		return request<UserResponse>("/auth/me");
	},
};

export { ApiError };
