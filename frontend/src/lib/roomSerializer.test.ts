import type { MemoryItem, Room } from "@/types/api";
import { describe, expect, it } from "vitest";
import { deserializeRoom, exportRoomJSON, parseRoomJSON, serializeRoom } from "./roomSerializer";

const mockRoom: Room = {
	id: "room-1",
	owner_id: "owner-1",
	name: "Test Room",
	description: "A test room",
	layout_data: null,
	created_at: "2026-01-01T00:00:00Z",
	updated_at: "2026-01-01T00:00:00Z",
};

const mockItems: MemoryItem[] = [
	{
		id: "item-1",
		room_id: "room-1",
		content: "Paris is the capital of France",
		image_url: null,
		position_x: 1.5,
		position_y: 0,
		position_z: 3.0,
		ease_factor: 2.5,
		interval: 1,
		repetitions: 0,
		last_reviewed_at: null,
		created_at: "2026-01-01T00:00:00Z",
		updated_at: "2026-01-01T00:00:00Z",
	},
	{
		id: "item-2",
		room_id: "room-1",
		content: "Tokyo is the capital of Japan",
		image_url: "https://example.com/tokyo.png",
		position_x: -2.0,
		position_y: 0,
		position_z: 1.5,
		ease_factor: 2.5,
		interval: 1,
		repetitions: 0,
		last_reviewed_at: null,
		created_at: "2026-01-01T00:00:00Z",
		updated_at: "2026-01-01T00:00:00Z",
	},
];

describe("serializeRoom", () => {
	it("converts room and items to serialized format", () => {
		const result = serializeRoom(mockRoom, mockItems);

		expect(result.id).toBe("room-1");
		expect(result.name).toBe("Test Room");
		expect(result.description).toBe("A test room");
		expect(result.items).toHaveLength(2);
		expect(result.items[0]?.position.x).toBe(1.5);
		expect(result.items[0]?.position.z).toBe(3.0);
	});

	it("handles empty items list", () => {
		const result = serializeRoom(mockRoom, []);
		expect(result.items).toHaveLength(0);
	});

	it("preserves image_url in serialized items", () => {
		const result = serializeRoom(mockRoom, mockItems);
		expect(result.items[0]?.image_url).toBeNull();
		expect(result.items[1]?.image_url).toBe("https://example.com/tokyo.png");
	});
});

describe("deserializeRoom", () => {
	it("converts serialized data back to room and items", () => {
		const serialized = serializeRoom(mockRoom, mockItems);
		const result = deserializeRoom(serialized);

		expect(result.room.name).toBe("Test Room");
		expect(result.items).toHaveLength(2);
		expect(result.items[0]?.content).toBe("Paris is the capital of France");
	});
});

describe("exportRoomJSON", () => {
	it("produces valid JSON string", () => {
		const json = exportRoomJSON(mockRoom, mockItems);
		const parsed: unknown = JSON.parse(json);
		expect(parsed).toBeDefined();
		expect(typeof parsed).toBe("object");
	});

	it("includes room name and items", () => {
		const json = exportRoomJSON(mockRoom, mockItems);
		const parsed = JSON.parse(json) as Record<string, unknown>;
		expect(parsed["name"]).toBe("Test Room");
		expect(Array.isArray(parsed["items"])).toBe(true);
	});
});

describe("parseRoomJSON", () => {
	it("parses valid room JSON", () => {
		const json = exportRoomJSON(mockRoom, mockItems);
		const result = parseRoomJSON(json);

		expect(result.name).toBe("Test Room");
		expect(result.items).toHaveLength(2);
	});

	it("throws on invalid JSON", () => {
		expect(() => parseRoomJSON("not json")).toThrow();
	});

	it("throws on missing name", () => {
		expect(() => parseRoomJSON('{"items": []}')).toThrow("missing or empty name");
	});

	it("throws on empty name", () => {
		expect(() => parseRoomJSON('{"name": "", "items": []}')).toThrow("missing or empty name");
	});

	it("throws on missing items", () => {
		expect(() => parseRoomJSON('{"name": "Room"}')).toThrow("items must be an array");
	});

	it("throws on non-array items", () => {
		expect(() => parseRoomJSON('{"name": "Room", "items": "not array"}')).toThrow("items must be an array");
	});

	it("throws on non-object input", () => {
		expect(() => parseRoomJSON('"just a string"')).toThrow("expected an object");
	});
});
