import * as THREE from "three";
import { afterEach, describe, expect, it, vi } from "vitest";

// jsdom has no WebGL context, so replace only WebGLRenderer with a lightweight
// stub and keep the rest of three real (geometries, materials, scene graph).
vi.mock("three", async (importOriginal) => {
	const actual = await importOriginal<typeof import("three")>();
	class FakeWebGLRenderer {
		domElement: HTMLCanvasElement;
		shadowMap = { enabled: false, type: 0 };
		constructor(params?: { canvas?: HTMLCanvasElement }) {
			this.domElement = params?.canvas ?? document.createElement("canvas");
		}
		setSize = vi.fn();
		setPixelRatio = vi.fn();
		render = vi.fn();
		dispose = vi.fn();
	}
	return { ...actual, WebGLRenderer: FakeWebGLRenderer };
});

// Imported after the mock is registered (vi.mock is hoisted by Vitest).
const { RoomScene } = await import("./RoomScene");

function makeCanvas(): HTMLCanvasElement {
	const canvas = document.createElement("canvas");
	Object.defineProperty(canvas, "clientWidth", { value: 800, configurable: true });
	Object.defineProperty(canvas, "clientHeight", { value: 600, configurable: true });
	return canvas;
}

describe("RoomScene", () => {
	afterEach(() => {
		vi.restoreAllMocks();
	});

	it("builds a scene populated with room geometry", () => {
		const room = new RoomScene(makeCanvas());
		expect(room.scene.children.length).toBeGreaterThan(0);
	});

	it("disposes geometries, materials and the renderer", () => {
		const geometryDispose = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
		const materialDispose = vi.spyOn(THREE.Material.prototype, "dispose");

		const room = new RoomScene(makeCanvas());
		const rendererDispose = room.renderer.dispose as ReturnType<typeof vi.fn>;

		room.dispose();

		expect(geometryDispose).toHaveBeenCalled();
		expect(materialDispose).toHaveBeenCalled();
		expect(rendererDispose).toHaveBeenCalled();
	});

	it("stops the render loop on dispose", () => {
		const cancelSpy = vi.spyOn(globalThis, "cancelAnimationFrame");
		vi.spyOn(globalThis, "requestAnimationFrame").mockReturnValue(42);

		const room = new RoomScene(makeCanvas());
		room.start();
		room.dispose();

		expect(cancelSpy).toHaveBeenCalledWith(42);
	});
});
