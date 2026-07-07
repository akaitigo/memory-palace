import * as THREE from "three";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ItemManager } from "./ItemManager";
import type { RoomDimensions } from "./RoomScene";

const DIMENSIONS: RoomDimensions = { width: 20, height: 4, depth: 20 };

/** A minimal 2D context stub — jsdom does not implement canvas 2D. */
function fakeContext(): CanvasRenderingContext2D {
	return {
		fillStyle: "",
		font: "",
		textAlign: "",
		textBaseline: "",
		fillRect: vi.fn(),
		roundRect: vi.fn(),
		fill: vi.fn(),
		fillText: vi.fn(),
	} as unknown as CanvasRenderingContext2D;
}

function makeManager() {
	const scene = new THREE.Scene();
	const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 100);
	const manager = new ItemManager(scene, camera, DIMENSIONS);
	return { manager, scene, camera };
}

describe("ItemManager", () => {
	beforeEach(() => {
		vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(fakeContext());
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it("removeItem returns false for an unknown id", () => {
		const { manager } = makeManager();
		expect(manager.removeItem("missing")).toBe(false);
	});

	it("removeItem disposes the item's geometries and materials", () => {
		const geometryDispose = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
		const materialDispose = vi.spyOn(THREE.Material.prototype, "dispose");

		const { manager, scene } = makeManager();
		manager.addItem("item-1", "Capital of France", new THREE.Vector3(1, 0, 1));
		// Placement indicator + item group.
		expect(scene.children).toHaveLength(2);

		const removed = manager.removeItem("item-1");

		expect(removed).toBe(true);
		expect(manager.getAllItems().size).toBe(0);
		expect(scene.children).toHaveLength(1); // only the placement indicator remains
		expect(geometryDispose).toHaveBeenCalled();
		expect(materialDispose).toHaveBeenCalled();
	});

	it("dispose releases all items and the placement indicator", () => {
		const geometryDispose = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
		const materialDispose = vi.spyOn(THREE.Material.prototype, "dispose");

		const { manager } = makeManager();
		manager.addItem("item-1", "One", new THREE.Vector3(1, 0, 1));
		manager.addItem("item-2", "Two", new THREE.Vector3(-1, 0, -1));
		expect(manager.getAllItems().size).toBe(2);

		manager.dispose();

		expect(manager.getAllItems().size).toBe(0);
		// Geometry disposed for both item markers and the placement indicator.
		expect(geometryDispose.mock.calls.length).toBeGreaterThanOrEqual(3);
		expect(materialDispose).toHaveBeenCalled();
	});
});
