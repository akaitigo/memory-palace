import * as THREE from "three";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FirstPersonControls } from "./FirstPersonControls";
import type { RoomDimensions } from "./RoomScene";

const DIMENSIONS: RoomDimensions = { width: 20, height: 4, depth: 20 };

function makeControls() {
	const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 100);
	const domElement = document.createElement("div");
	const controls = new FirstPersonControls(camera, domElement, DIMENSIONS);
	return { controls, camera, domElement };
}

describe("FirstPersonControls", () => {
	afterEach(() => {
		vi.restoreAllMocks();
	});

	it("starts unlocked", () => {
		const { controls } = makeControls();
		expect(controls.getIsLocked()).toBe(false);
		controls.disconnect();
	});

	it("removes every event listener on disconnect", () => {
		const documentRemove = vi.spyOn(document, "removeEventListener");
		const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 100);
		const domElement = document.createElement("div");
		const domRemove = vi.spyOn(domElement, "removeEventListener");

		const controls = new FirstPersonControls(camera, domElement, DIMENSIONS);
		controls.disconnect();

		expect(documentRemove).toHaveBeenCalledWith("mousemove", expect.any(Function));
		expect(documentRemove).toHaveBeenCalledWith("keydown", expect.any(Function));
		expect(documentRemove).toHaveBeenCalledWith("keyup", expect.any(Function));
		expect(documentRemove).toHaveBeenCalledWith("pointerlockchange", expect.any(Function));
		expect(domRemove).toHaveBeenCalledWith("click", expect.any(Function));
	});

	it("removes the same handler references it added", () => {
		const added: Record<string, EventListenerOrEventListenerObject> = {};
		const removed: Record<string, EventListenerOrEventListenerObject> = {};
		vi.spyOn(document, "addEventListener").mockImplementation((type, handler) => {
			added[type] = handler as EventListenerOrEventListenerObject;
		});
		vi.spyOn(document, "removeEventListener").mockImplementation((type, handler) => {
			removed[type] = handler as EventListenerOrEventListenerObject;
		});

		const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 100);
		const controls = new FirstPersonControls(camera, document.createElement("div"), DIMENSIONS);
		controls.disconnect();

		for (const type of ["mousemove", "keydown", "keyup", "pointerlockchange"]) {
			expect(removed[type]).toBe(added[type]);
		}
	});
});
