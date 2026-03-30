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
