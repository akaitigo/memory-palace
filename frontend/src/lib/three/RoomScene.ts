/**
 * Three.js room scene manager.
 *
 * Handles renderer, camera, scene, lighting, and room geometry.
 * Designed for first-person navigation using PointerLockControls-like behavior.
 */

import * as THREE from "three";

/** Room geometry dimensions */
export interface RoomDimensions {
	width: number;
	height: number;
	depth: number;
}

/** Default room dimensions */
const DEFAULT_DIMENSIONS: RoomDimensions = {
	width: 20,
	height: 4,
	depth: 20,
};

export class RoomScene {
	readonly scene: THREE.Scene;
	readonly camera: THREE.PerspectiveCamera;
	readonly renderer: THREE.WebGLRenderer;

	private animationId: number | null = null;
	private readonly dimensions: RoomDimensions;

	constructor(canvas: HTMLCanvasElement, dimensions?: Partial<RoomDimensions>) {
		this.dimensions = { ...DEFAULT_DIMENSIONS, ...dimensions };

		// Scene
		this.scene = new THREE.Scene();
		this.scene.background = new THREE.Color(0x1a1a2e);
		this.scene.fog = new THREE.Fog(0x1a1a2e, 15, 35);

		// Camera
		this.camera = new THREE.PerspectiveCamera(70, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
		this.camera.position.set(0, 1.6, this.dimensions.depth / 2 - 1);

		// Renderer
		this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
		this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
		this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
		this.renderer.shadowMap.enabled = true;
		this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

		this.setupLighting();
		this.buildRoom();
	}

	private setupLighting(): void {
		// Ambient
		const ambient = new THREE.AmbientLight(0x404060, 0.6);
		this.scene.add(ambient);

		// Main directional light
		const directional = new THREE.DirectionalLight(0xffffff, 0.8);
		directional.position.set(5, this.dimensions.height - 0.5, 5);
		directional.castShadow = true;
		directional.shadow.mapSize.width = 1024;
		directional.shadow.mapSize.height = 1024;
		this.scene.add(directional);

		// Fill light
		const fill = new THREE.PointLight(0x8888ff, 0.3, 30);
		fill.position.set(-3, this.dimensions.height - 1, -3);
		this.scene.add(fill);
	}

	private buildRoom(): void {
		const { width, height, depth } = this.dimensions;

		// Floor
		const floorGeometry = new THREE.PlaneGeometry(width, depth);
		const floorMaterial = new THREE.MeshStandardMaterial({
			color: 0x2a2a4a,
			roughness: 0.8,
			metalness: 0.2,
		});
		const floor = new THREE.Mesh(floorGeometry, floorMaterial);
		floor.rotation.x = -Math.PI / 2;
		floor.receiveShadow = true;
		floor.userData["type"] = "floor";
		this.scene.add(floor);

		// Grid helper on floor
		const grid = new THREE.GridHelper(width, width, 0x444466, 0x333355);
		grid.position.y = 0.01;
		this.scene.add(grid);

		// Walls
		const wallMaterial = new THREE.MeshStandardMaterial({
			color: 0x3a3a5c,
			roughness: 0.9,
			metalness: 0.1,
			side: THREE.DoubleSide,
		});

		// Back wall
		const backWall = new THREE.Mesh(new THREE.PlaneGeometry(width, height), wallMaterial);
		backWall.position.set(0, height / 2, -depth / 2);
		backWall.receiveShadow = true;
		this.scene.add(backWall);

		// Front wall
		const frontWall = new THREE.Mesh(new THREE.PlaneGeometry(width, height), wallMaterial);
		frontWall.position.set(0, height / 2, depth / 2);
		frontWall.rotation.y = Math.PI;
		frontWall.receiveShadow = true;
		this.scene.add(frontWall);

		// Left wall
		const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(depth, height), wallMaterial);
		leftWall.position.set(-width / 2, height / 2, 0);
		leftWall.rotation.y = Math.PI / 2;
		leftWall.receiveShadow = true;
		this.scene.add(leftWall);

		// Right wall
		const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(depth, height), wallMaterial);
		rightWall.position.set(width / 2, height / 2, 0);
		rightWall.rotation.y = -Math.PI / 2;
		rightWall.receiveShadow = true;
		this.scene.add(rightWall);
	}

	/** Start the render loop */
	start(onFrame?: () => void): void {
		const animate = (): void => {
			this.animationId = requestAnimationFrame(animate);
			onFrame?.();
			this.renderer.render(this.scene, this.camera);
		};
		animate();
	}

	/** Stop the render loop */
	stop(): void {
		if (this.animationId !== null) {
			cancelAnimationFrame(this.animationId);
			this.animationId = null;
		}
	}

	/** Handle window resize */
	handleResize(width: number, height: number): void {
		this.camera.aspect = width / height;
		this.camera.updateProjectionMatrix();
		this.renderer.setSize(width, height);
	}

	/** Get the room dimensions */
	getDimensions(): Readonly<RoomDimensions> {
		return { ...this.dimensions };
	}

	/** Dispose of all Three.js resources */
	dispose(): void {
		this.stop();
		this.scene.traverse((object) => {
			if (object instanceof THREE.Mesh) {
				object.geometry.dispose();
				const material = object.material;
				if (Array.isArray(material)) {
					for (const mat of material) {
						mat.dispose();
					}
				} else {
					material.dispose();
				}
			}
		});
		this.renderer.dispose();
	}
}
