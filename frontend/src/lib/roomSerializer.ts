/**
 * Room data serialization/deserialization utilities.
 *
 * Converts between backend API data and Three.js scene representation.
 */

import type { MemoryItem, Room } from "@/types/api";

/** Serialized room data for JSON export/import */
export interface SerializedRoom {
	id: string;
	name: string;
	description: string | null;
	items: SerializedItem[];
}

export interface SerializedItem {
	id: string;
	content: string;
	position: { x: number; y: number; z: number };
	image_url: string | null;
}

/** Convert API room + items to serialized format */
export function serializeRoom(room: Room, items: MemoryItem[]): SerializedRoom {
	return {
		id: room.id,
		name: room.name,
		description: room.description,
		items: items.map((item) => ({
			id: item.id,
			content: item.content,
			position: {
				x: item.position_x,
				y: item.position_y,
				z: item.position_z,
			},
			image_url: item.image_url,
		})),
	};
}

/** Convert serialized format back to API-compatible structures */
export function deserializeRoom(data: SerializedRoom): { room: Partial<Room>; items: SerializedItem[] } {
	return {
		room: {
			id: data.id,
			name: data.name,
			description: data.description,
		},
		items: data.items,
	};
}

/** Export room data as JSON string */
export function exportRoomJSON(room: Room, items: MemoryItem[]): string {
	return JSON.stringify(serializeRoom(room, items), null, 2);
}

/** Parse and validate imported room JSON */
export function parseRoomJSON(json: string): SerializedRoom {
	const parsed: unknown = JSON.parse(json);

	if (typeof parsed !== "object" || parsed === null) {
		throw new Error("Invalid room data: expected an object");
	}

	const data = parsed as Record<string, unknown>;

	if (typeof data["name"] !== "string" || data["name"].length === 0) {
		throw new Error("Invalid room data: missing or empty name");
	}

	if (!Array.isArray(data["items"])) {
		throw new Error("Invalid room data: items must be an array");
	}

	return data as unknown as SerializedRoom;
}
