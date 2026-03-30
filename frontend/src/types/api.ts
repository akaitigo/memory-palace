/**
 * API response types matching the backend Pydantic schemas.
 */

export interface Position {
	x: number;
	y: number;
	z: number;
}

export interface Room {
	id: string;
	owner_id: string;
	name: string;
	description: string | null;
	layout_data: Record<string, unknown> | null;
	created_at: string;
	updated_at: string;
}

export interface RoomCreateRequest {
	name: string;
	description?: string | null;
	layout_data?: Record<string, unknown> | null;
}

export interface RoomUpdateRequest {
	name?: string;
	description?: string | null;
	layout_data?: Record<string, unknown> | null;
}

export interface MemoryItem {
	id: string;
	room_id: string;
	content: string;
	image_url: string | null;
	position_x: number;
	position_y: number;
	position_z: number;
	ease_factor: number;
	interval: number;
	repetitions: number;
	last_reviewed_at: string | null;
	created_at: string;
	updated_at: string;
}

export interface MemoryItemCreateRequest {
	content: string;
	image_url?: string | null;
	position: Position;
}

export interface MemoryItemUpdateRequest {
	content?: string;
	image_url?: string | null;
	position?: Position;
}

// =============================================================================
// Review types
// =============================================================================

export interface ReviewRecordCreate {
	memory_item_id: string;
	quality: number;
	response_time_ms: number;
}

export interface ReviewRecordResponse {
	id: string;
	session_id: string;
	memory_item_id: string;
	quality: number;
	response_time_ms: number;
	reviewed_at: string;
}

export interface RoomStatsResponse {
	total_items: number;
	reviewed_items: number;
	mastered_items: number;
	learning_items: number;
	new_items: number;
	average_ease_factor: number | null;
	total_reviews: number;
	average_quality: number | null;
	reviews_today: number;
}

export interface DailyStatsEntry {
	date: string;
	review_count: number;
	average_quality: number | null;
	correct_rate: number | null;
}

export interface DailyStatsResponse {
	entries: DailyStatsEntry[];
}

export interface ForgettingCurvePoint {
	days_since_review: number;
	retention: number;
}

export interface ForgettingCurveItem {
	item_id: string;
	content: string;
	stability: number;
	curve: ForgettingCurvePoint[];
}

export interface ForgettingCurveResponse {
	items: ForgettingCurveItem[];
}
