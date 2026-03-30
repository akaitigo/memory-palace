/**
 * First-person camera controls using PointerLock API.
 *
 * WASD movement + mouse look (activated by clicking on the canvas).
 * Movement is constrained within room boundaries.
 */

import * as THREE from "three";
import type { RoomDimensions } from "./RoomScene";

/** Movement speed in units per second */
const MOVE_SPEED = 5.0;

/** Mouse sensitivity (radians per pixel) */
const MOUSE_SENSITIVITY = 0.002;

/** Camera height (eye level) */
const EYE_HEIGHT = 1.6;

/** Margin from walls */
const WALL_MARGIN = 0.5;

interface KeyState {
	forward: boolean;
	backward: boolean;
	left: boolean;
	right: boolean;
}

export class FirstPersonControls {
	private readonly camera: THREE.PerspectiveCamera;
	private readonly domElement: HTMLElement;
	private readonly dimensions: RoomDimensions;
	private readonly euler: THREE.Euler;
	private readonly velocity: THREE.Vector3;
	private readonly direction: THREE.Vector3;
	private readonly keys: KeyState;
	private isLocked: boolean;
	private prevTime: number;

	private readonly onMouseMoveBound: (e: MouseEvent) => void;
	private readonly onKeyDownBound: (e: KeyboardEvent) => void;
	private readonly onKeyUpBound: (e: KeyboardEvent) => void;
	private readonly onPointerLockChangeBound: () => void;
	private readonly onClickBound: () => void;

	constructor(camera: THREE.PerspectiveCamera, domElement: HTMLElement, dimensions: RoomDimensions) {
		this.camera = camera;
		this.domElement = domElement;
		this.dimensions = dimensions;
		this.euler = new THREE.Euler(0, 0, 0, "YXZ");
		this.velocity = new THREE.Vector3();
		this.direction = new THREE.Vector3();
		this.keys = { forward: false, backward: false, left: false, right: false };
		this.isLocked = false;
		this.prevTime = performance.now();

		this.onMouseMoveBound = this.onMouseMove.bind(this);
		this.onKeyDownBound = this.onKeyDown.bind(this);
		this.onKeyUpBound = this.onKeyUp.bind(this);
		this.onPointerLockChangeBound = this.onPointerLockChange.bind(this);
		this.onClickBound = this.onClick.bind(this);

		this.connect();
	}

	private connect(): void {
		document.addEventListener("mousemove", this.onMouseMoveBound);
		document.addEventListener("keydown", this.onKeyDownBound);
		document.addEventListener("keyup", this.onKeyUpBound);
		document.addEventListener("pointerlockchange", this.onPointerLockChangeBound);
		this.domElement.addEventListener("click", this.onClickBound);
	}

	disconnect(): void {
		document.removeEventListener("mousemove", this.onMouseMoveBound);
		document.removeEventListener("keydown", this.onKeyDownBound);
		document.removeEventListener("keyup", this.onKeyUpBound);
		document.removeEventListener("pointerlockchange", this.onPointerLockChangeBound);
		this.domElement.removeEventListener("click", this.onClickBound);

		if (document.pointerLockElement === this.domElement) {
			document.exitPointerLock();
		}
	}

	private onClick(): void {
		this.domElement.requestPointerLock();
	}

	private onPointerLockChange(): void {
		this.isLocked = document.pointerLockElement === this.domElement;
		if (!this.isLocked) {
			this.keys.forward = false;
			this.keys.backward = false;
			this.keys.left = false;
			this.keys.right = false;
		}
	}

	private onMouseMove(event: MouseEvent): void {
		if (!this.isLocked) return;

		this.euler.setFromQuaternion(this.camera.quaternion);
		this.euler.y -= event.movementX * MOUSE_SENSITIVITY;
		this.euler.x -= event.movementY * MOUSE_SENSITIVITY;
		// Clamp vertical look to prevent flipping
		this.euler.x = Math.max(-Math.PI / 2 + 0.01, Math.min(Math.PI / 2 - 0.01, this.euler.x));

		this.camera.quaternion.setFromEuler(this.euler);
	}

	private onKeyDown(event: KeyboardEvent): void {
		if (!this.isLocked) return;

		switch (event.code) {
			case "KeyW":
			case "ArrowUp":
				this.keys.forward = true;
				break;
			case "KeyS":
			case "ArrowDown":
				this.keys.backward = true;
				break;
			case "KeyA":
			case "ArrowLeft":
				this.keys.left = true;
				break;
			case "KeyD":
			case "ArrowRight":
				this.keys.right = true;
				break;
		}
	}

	private onKeyUp(event: KeyboardEvent): void {
		switch (event.code) {
			case "KeyW":
			case "ArrowUp":
				this.keys.forward = false;
				break;
			case "KeyS":
			case "ArrowDown":
				this.keys.backward = false;
				break;
			case "KeyA":
			case "ArrowLeft":
				this.keys.left = false;
				break;
			case "KeyD":
			case "ArrowRight":
				this.keys.right = false;
				break;
		}
	}

	/** Update camera position based on key state. Call each frame. */
	update(): void {
		const time = performance.now();
		const delta = (time - this.prevTime) / 1000;
		this.prevTime = time;

		if (!this.isLocked) return;

		// Apply friction
		this.velocity.x -= this.velocity.x * 10.0 * delta;
		this.velocity.z -= this.velocity.z * 10.0 * delta;

		// Calculate direction
		this.direction.z = Number(this.keys.forward) - Number(this.keys.backward);
		this.direction.x = Number(this.keys.right) - Number(this.keys.left);
		this.direction.normalize();

		if (this.keys.forward || this.keys.backward) {
			this.velocity.z -= this.direction.z * MOVE_SPEED * delta;
		}
		if (this.keys.left || this.keys.right) {
			this.velocity.x -= this.direction.x * MOVE_SPEED * delta;
		}

		// Move camera
		const forward = new THREE.Vector3();
		this.camera.getWorldDirection(forward);
		forward.y = 0;
		forward.normalize();

		const right = new THREE.Vector3();
		right.crossVectors(this.camera.up, forward).normalize();

		this.camera.position.addScaledVector(forward, -this.velocity.z * delta);
		this.camera.position.addScaledVector(right, -this.velocity.x * delta);

		// Constrain to room boundaries
		const halfWidth = this.dimensions.width / 2 - WALL_MARGIN;
		const halfDepth = this.dimensions.depth / 2 - WALL_MARGIN;
		this.camera.position.x = Math.max(-halfWidth, Math.min(halfWidth, this.camera.position.x));
		this.camera.position.z = Math.max(-halfDepth, Math.min(halfDepth, this.camera.position.z));
		this.camera.position.y = EYE_HEIGHT;
	}

	/** Check if pointer is currently locked */
	getIsLocked(): boolean {
		return this.isLocked;
	}
}
