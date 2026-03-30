/**
 * Manages 3D memory item objects in the room scene.
 *
 * Handles creation, selection, movement, and deletion of item markers.
 * Uses Raycaster for click-based interaction.
 */

import * as THREE from "three";
import type { RoomDimensions } from "./RoomScene";

/** Visual representation of a memory item in 3D space */
export interface Item3D {
	id: string;
	content: string;
	mesh: THREE.Mesh;
	label: THREE.Sprite;
	group: THREE.Group;
}

/** Callback types for item events */
export interface ItemManagerCallbacks {
	onItemPlaced?: (position: THREE.Vector3) => void;
	onItemSelected?: (itemId: string) => void;
	onItemDeselected?: () => void;
}

/** Item marker geometry constants */
const MARKER_RADIUS = 0.2;
const MARKER_HEIGHT = 0.5;
const MARKER_SEGMENTS = 8;
const LABEL_SCALE = 0.8;
const LABEL_Y_OFFSET = 0.8;

/** Colors */
const COLOR_DEFAULT = 0x00aaff;
const COLOR_SELECTED = 0xffaa00;
const COLOR_HOVER = 0x44ccff;

export class ItemManager {
	private readonly scene: THREE.Scene;
	private readonly camera: THREE.PerspectiveCamera;
	private readonly raycaster: THREE.Raycaster;
	private readonly mouse: THREE.Vector2;
	private readonly dimensions: RoomDimensions;
	private readonly items: Map<string, Item3D>;
	private readonly callbacks: ItemManagerCallbacks;

	private selectedItemId: string | null = null;
	private hoveredItemId: string | null = null;
	private placementMode = false;

	/** Placement indicator (crosshair on the floor) */
	private readonly placementIndicator: THREE.Mesh;

	constructor(
		scene: THREE.Scene,
		camera: THREE.PerspectiveCamera,
		dimensions: RoomDimensions,
		callbacks: ItemManagerCallbacks = {},
	) {
		this.scene = scene;
		this.camera = camera;
		this.raycaster = new THREE.Raycaster();
		this.mouse = new THREE.Vector2();
		this.dimensions = dimensions;
		this.items = new Map();
		this.callbacks = callbacks;

		// Create placement indicator (hidden by default)
		const indicatorGeo = new THREE.RingGeometry(0.15, 0.25, 16);
		const indicatorMat = new THREE.MeshBasicMaterial({
			color: 0x00ff88,
			side: THREE.DoubleSide,
			transparent: true,
			opacity: 0.7,
		});
		this.placementIndicator = new THREE.Mesh(indicatorGeo, indicatorMat);
		this.placementIndicator.rotation.x = -Math.PI / 2;
		this.placementIndicator.visible = false;
		this.scene.add(this.placementIndicator);
	}

	/** Add a memory item to the scene */
	addItem(id: string, content: string, position: THREE.Vector3): Item3D {
		const group = new THREE.Group();
		group.position.copy(position);

		// Marker mesh (cylinder with sphere on top)
		const markerGeo = new THREE.CylinderGeometry(MARKER_RADIUS * 0.5, MARKER_RADIUS, MARKER_HEIGHT, MARKER_SEGMENTS);
		const markerMat = new THREE.MeshStandardMaterial({
			color: COLOR_DEFAULT,
			emissive: COLOR_DEFAULT,
			emissiveIntensity: 0.3,
			roughness: 0.4,
			metalness: 0.6,
		});
		const mesh = new THREE.Mesh(markerGeo, markerMat);
		mesh.position.y = MARKER_HEIGHT / 2;
		mesh.castShadow = true;
		mesh.userData["itemId"] = id;
		group.add(mesh);

		// Sphere top cap
		const sphereGeo = new THREE.SphereGeometry(MARKER_RADIUS * 0.6, MARKER_SEGMENTS, MARKER_SEGMENTS);
		const sphere = new THREE.Mesh(sphereGeo, markerMat);
		sphere.position.y = MARKER_HEIGHT;
		sphere.castShadow = true;
		sphere.userData["itemId"] = id;
		group.add(sphere);

		// Text label sprite
		const label = this.createLabelSprite(content);
		label.position.y = MARKER_HEIGHT + LABEL_Y_OFFSET;
		group.add(label);

		this.scene.add(group);

		const item3D: Item3D = { id, content, mesh, label, group };
		this.items.set(id, item3D);
		return item3D;
	}

	/** Remove a memory item from the scene */
	removeItem(id: string): boolean {
		const item = this.items.get(id);
		if (!item) return false;

		if (this.selectedItemId === id) {
			this.selectedItemId = null;
			this.callbacks.onItemDeselected?.();
		}

		this.scene.remove(item.group);

		// Dispose geometries and materials
		item.group.traverse((child) => {
			if (child instanceof THREE.Mesh) {
				child.geometry.dispose();
				if (Array.isArray(child.material)) {
					for (const mat of child.material) {
						mat.dispose();
					}
				} else {
					child.material.dispose();
				}
			}
			if (child instanceof THREE.Sprite) {
				child.material.map?.dispose();
				child.material.dispose();
			}
		});

		this.items.delete(id);
		return true;
	}

	/** Update item position */
	moveItem(id: string, position: THREE.Vector3): boolean {
		const item = this.items.get(id);
		if (!item) return false;

		const clampedPos = this.clampToRoom(position);
		item.group.position.copy(clampedPos);
		return true;
	}

	/** Update item label text */
	updateItemContent(id: string, content: string): boolean {
		const item = this.items.get(id);
		if (!item) return false;

		// Remove old label
		item.group.remove(item.label);
		item.label.material.map?.dispose();
		item.label.material.dispose();

		// Create new label
		const newLabel = this.createLabelSprite(content);
		newLabel.position.y = MARKER_HEIGHT + LABEL_Y_OFFSET;
		item.group.add(newLabel);
		item.label = newLabel;
		item.content = content;

		return true;
	}

	/** Handle mouse move for hover effects and placement indicator */
	handleMouseMove(event: MouseEvent, canvasRect: DOMRect): void {
		this.mouse.x = ((event.clientX - canvasRect.left) / canvasRect.width) * 2 - 1;
		this.mouse.y = -((event.clientY - canvasRect.top) / canvasRect.height) * 2 + 1;

		if (this.placementMode) {
			this.updatePlacementIndicator();
		} else {
			this.updateHover();
		}
	}

	/** Handle click for item selection or placement */
	handleClick(event: MouseEvent, canvasRect: DOMRect): void {
		this.mouse.x = ((event.clientX - canvasRect.left) / canvasRect.width) * 2 - 1;
		this.mouse.y = -((event.clientY - canvasRect.top) / canvasRect.height) * 2 + 1;

		if (this.placementMode) {
			this.handlePlacement();
			return;
		}

		this.handleSelection();
	}

	/** Toggle placement mode */
	setPlacementMode(enabled: boolean): void {
		this.placementMode = enabled;
		this.placementIndicator.visible = false;

		if (enabled && this.selectedItemId) {
			this.deselectItem();
		}
	}

	/** Get whether in placement mode */
	isInPlacementMode(): boolean {
		return this.placementMode;
	}

	/** Get currently selected item ID */
	getSelectedItemId(): string | null {
		return this.selectedItemId;
	}

	/** Get all items */
	getAllItems(): ReadonlyMap<string, Item3D> {
		return this.items;
	}

	/** Get item position */
	getItemPosition(id: string): THREE.Vector3 | null {
		const item = this.items.get(id);
		return item ? item.group.position.clone() : null;
	}

	/** Dispose all resources */
	dispose(): void {
		for (const [id] of this.items) {
			this.removeItem(id);
		}
		this.placementIndicator.geometry.dispose();
		if (this.placementIndicator.material instanceof THREE.Material) {
			this.placementIndicator.material.dispose();
		}
	}

	// =========================================================================
	// Private methods
	// =========================================================================

	private createLabelSprite(text: string): THREE.Sprite {
		const canvas = document.createElement("canvas");
		const ctx = canvas.getContext("2d");
		if (!ctx) {
			throw new Error("Failed to create 2D canvas context for label");
		}

		canvas.width = 256;
		canvas.height = 64;

		// Background
		ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
		ctx.roundRect(0, 0, canvas.width, canvas.height, 8);
		ctx.fill();

		// Text (truncate to fit)
		ctx.fillStyle = "#ffffff";
		ctx.font = "bold 20px sans-serif";
		ctx.textAlign = "center";
		ctx.textBaseline = "middle";

		const displayText = text.length > 25 ? `${text.substring(0, 22)}...` : text;
		ctx.fillText(displayText, canvas.width / 2, canvas.height / 2);

		const texture = new THREE.CanvasTexture(canvas);
		const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
		const sprite = new THREE.Sprite(material);
		sprite.scale.set(LABEL_SCALE * (canvas.width / canvas.height), LABEL_SCALE, 1);

		return sprite;
	}

	private getFloorIntersection(): THREE.Vector3 | null {
		this.raycaster.setFromCamera(this.mouse, this.camera);

		// Intersect with the floor plane (y = 0)
		const floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
		const target = new THREE.Vector3();
		const hit = this.raycaster.ray.intersectPlane(floorPlane, target);

		if (!hit) return null;
		return this.clampToRoom(target);
	}

	private getItemIntersection(): string | null {
		this.raycaster.setFromCamera(this.mouse, this.camera);

		const meshes: THREE.Object3D[] = [];
		for (const item of this.items.values()) {
			item.group.traverse((child) => {
				if (child instanceof THREE.Mesh) {
					meshes.push(child);
				}
			});
		}

		const intersects = this.raycaster.intersectObjects(meshes);
		if (intersects.length > 0) {
			const hitObject = intersects[0]?.object;
			const itemId = hitObject?.userData?.["itemId"] as string | undefined;
			return itemId ?? null;
		}
		return null;
	}

	private updatePlacementIndicator(): void {
		const point = this.getFloorIntersection();
		if (point) {
			this.placementIndicator.position.set(point.x, 0.02, point.z);
			this.placementIndicator.visible = true;
		} else {
			this.placementIndicator.visible = false;
		}
	}

	private updateHover(): void {
		const hitId = this.getItemIntersection();

		// Unhover previous
		if (this.hoveredItemId && this.hoveredItemId !== hitId) {
			const prev = this.items.get(this.hoveredItemId);
			if (prev && this.hoveredItemId !== this.selectedItemId) {
				this.setItemColor(prev, COLOR_DEFAULT);
			}
			this.hoveredItemId = null;
		}

		// Hover new
		if (hitId && hitId !== this.selectedItemId) {
			const item = this.items.get(hitId);
			if (item) {
				this.setItemColor(item, COLOR_HOVER);
				this.hoveredItemId = hitId;
			}
		}
	}

	private handlePlacement(): void {
		const point = this.getFloorIntersection();
		if (point) {
			this.placementMode = false;
			this.placementIndicator.visible = false;
			this.callbacks.onItemPlaced?.(point);
		}
	}

	private handleSelection(): void {
		const hitId = this.getItemIntersection();

		if (hitId) {
			// Select item
			if (this.selectedItemId && this.selectedItemId !== hitId) {
				this.deselectItem();
			}
			const item = this.items.get(hitId);
			if (item) {
				this.selectedItemId = hitId;
				this.setItemColor(item, COLOR_SELECTED);
				this.callbacks.onItemSelected?.(hitId);
			}
		} else if (this.selectedItemId) {
			// Deselect
			this.deselectItem();
		}
	}

	private deselectItem(): void {
		if (this.selectedItemId) {
			const item = this.items.get(this.selectedItemId);
			if (item) {
				this.setItemColor(item, COLOR_DEFAULT);
			}
			this.selectedItemId = null;
			this.callbacks.onItemDeselected?.();
		}
	}

	private setItemColor(item: Item3D, color: number): void {
		item.group.traverse((child) => {
			if (child instanceof THREE.Mesh) {
				const mat = child.material;
				if (mat instanceof THREE.MeshStandardMaterial) {
					mat.color.setHex(color);
					mat.emissive.setHex(color);
				}
			}
		});
	}

	private clampToRoom(position: THREE.Vector3): THREE.Vector3 {
		const halfWidth = this.dimensions.width / 2 - 0.3;
		const halfDepth = this.dimensions.depth / 2 - 0.3;
		return new THREE.Vector3(
			Math.max(-halfWidth, Math.min(halfWidth, position.x)),
			0,
			Math.max(-halfDepth, Math.min(halfDepth, position.z)),
		);
	}
}
