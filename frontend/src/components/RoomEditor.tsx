/**
 * 3D Room Editor component.
 *
 * Integrates Three.js scene with React state management.
 * Handles room rendering, item placement, selection, and CRUD operations.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { itemApi, roomApi } from "@/lib/api";
import { FirstPersonControls } from "@/lib/three/FirstPersonControls";
import { ItemManager, type ItemManagerCallbacks } from "@/lib/three/ItemManager";
import { RoomScene } from "@/lib/three/RoomScene";
import type { MemoryItem, Room } from "@/types/api";

/** Props for the RoomEditor component */
export interface RoomEditorProps {
	roomId: string;
}

interface EditorState {
	room: Room | null;
	items: MemoryItem[];
	selectedItemId: string | null;
	isPlacementMode: boolean;
	isPointerLocked: boolean;
	loading: boolean;
	error: string | null;
	newItemContent: string;
	editContent: string;
}

const INITIAL_STATE: EditorState = {
	room: null,
	items: [],
	selectedItemId: null,
	isPlacementMode: false,
	isPointerLocked: false,
	loading: true,
	error: null,
	newItemContent: "",
	editContent: "",
};

export function RoomEditor({ roomId }: RoomEditorProps): React.JSX.Element {
	const canvasRef = useRef<HTMLCanvasElement>(null);
	const containerRef = useRef<HTMLDivElement>(null);
	const sceneRef = useRef<RoomScene | null>(null);
	const controlsRef = useRef<FirstPersonControls | null>(null);
	const itemManagerRef = useRef<ItemManager | null>(null);

	const [state, setState] = useState<EditorState>(INITIAL_STATE);
	const handleItemPlacedRef = useRef<((position: THREE.Vector3) => Promise<void>) | null>(null);

	// Partial state updater
	const updateState = useCallback((partial: Partial<EditorState>) => {
		setState((prev) => ({ ...prev, ...partial }));
	}, []);

	// =========================================================================
	// Data fetching
	// =========================================================================

	const loadRoom = useCallback(async () => {
		try {
			updateState({ loading: true, error: null });
			const [room, items] = await Promise.all([roomApi.get(roomId), itemApi.list(roomId)]);
			updateState({ room, items, loading: false });
			return { room, items };
		} catch (err) {
			const message = err instanceof Error ? err.message : "Failed to load room";
			updateState({ error: message, loading: false });
			return null;
		}
	}, [roomId, updateState]);

	// =========================================================================
	// Three.js initialization
	// =========================================================================

	useEffect(() => {
		const canvas = canvasRef.current;
		const container = containerRef.current;
		if (!(canvas && container)) return;

		const roomScene = new RoomScene(canvas);
		sceneRef.current = roomScene;

		const dimensions = roomScene.getDimensions();

		const controls = new FirstPersonControls(roomScene.camera, canvas, dimensions);
		controlsRef.current = controls;

		const callbacks: ItemManagerCallbacks = {
			onItemPlaced: (position: THREE.Vector3) => {
				setState((prev) => {
					if (prev.newItemContent.trim().length === 0) return prev;
					// Will be handled in placement handler
					return { ...prev, isPlacementMode: false };
				});
				handleItemPlacedRef.current?.(position);
			},
			onItemSelected: (itemId: string) => {
				setState((prev) => {
					const item = prev.items.find((i) => i.id === itemId);
					return {
						...prev,
						selectedItemId: itemId,
						editContent: item?.content ?? "",
					};
				});
			},
			onItemDeselected: () => {
				setState((prev) => ({
					...prev,
					selectedItemId: null,
					editContent: "",
				}));
			},
		};

		const itemMgr = new ItemManager(roomScene.scene, roomScene.camera, dimensions, callbacks);
		itemManagerRef.current = itemMgr;

		// Start render loop
		roomScene.start(() => {
			controls.update();
			updateState({ isPointerLocked: controls.getIsLocked() });
		});

		// Handle resize
		const resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				const { width, height } = entry.contentRect;
				if (width > 0 && height > 0) {
					roomScene.handleResize(width, height);
				}
			}
		});
		resizeObserver.observe(container);

		// Handle mouse events (only when not pointer-locked)
		const handleMouseMove = (event: MouseEvent): void => {
			if (controls.getIsLocked()) return;
			const rect = canvas.getBoundingClientRect();
			itemMgr.handleMouseMove(event, rect);
		};

		const handleClick = (event: MouseEvent): void => {
			if (controls.getIsLocked()) return;
			const rect = canvas.getBoundingClientRect();
			itemMgr.handleClick(event, rect);
		};

		canvas.addEventListener("mousemove", handleMouseMove);
		canvas.addEventListener("click", handleClick);

		// Load data and sync to 3D scene
		loadRoom().then((data) => {
			if (data) {
				for (const item of data.items) {
					itemMgr.addItem(item.id, item.content, new THREE.Vector3(item.position_x, 0, item.position_z));
				}
			}
		});

		return () => {
			canvas.removeEventListener("mousemove", handleMouseMove);
			canvas.removeEventListener("click", handleClick);
			resizeObserver.disconnect();
			controls.disconnect();
			itemMgr.dispose();
			roomScene.dispose();
			sceneRef.current = null;
			controlsRef.current = null;
			itemManagerRef.current = null;
		};
	}, [loadRoom, updateState]);

	// =========================================================================
	// Item CRUD handlers
	// =========================================================================

	const handleItemPlaced = useCallback(
		async (position: THREE.Vector3): Promise<void> => {
			const content = state.newItemContent.trim();
			if (content.length === 0 || content.length > 500) return;

			try {
				const newItem = await itemApi.create(roomId, {
					content,
					position: { x: position.x, y: position.y, z: position.z },
				});

				itemManagerRef.current?.addItem(
					newItem.id,
					newItem.content,
					new THREE.Vector3(newItem.position_x, 0, newItem.position_z),
				);

				updateState({
					items: [...state.items, newItem],
					newItemContent: "",
					isPlacementMode: false,
				});
			} catch (err) {
				const message = err instanceof Error ? err.message : "Failed to create item";
				updateState({ error: message });
			}
		},
		[roomId, state.newItemContent, state.items, updateState],
	);
	handleItemPlacedRef.current = handleItemPlaced;

	const handleDeleteItem = async (): Promise<void> => {
		if (!state.selectedItemId) return;

		try {
			await itemApi.delete(roomId, state.selectedItemId);
			itemManagerRef.current?.removeItem(state.selectedItemId);

			updateState({
				items: state.items.filter((i) => i.id !== state.selectedItemId),
				selectedItemId: null,
				editContent: "",
			});
		} catch (err) {
			const message = err instanceof Error ? err.message : "Failed to delete item";
			updateState({ error: message });
		}
	};

	const handleUpdateItem = async (): Promise<void> => {
		if (!state.selectedItemId) return;

		const content = state.editContent.trim();
		if (content.length === 0 || content.length > 500) return;

		try {
			const updatedItem = await itemApi.update(roomId, state.selectedItemId, { content });
			itemManagerRef.current?.updateItemContent(state.selectedItemId, content);

			updateState({
				items: state.items.map((i) => (i.id === state.selectedItemId ? updatedItem : i)),
				editContent: content,
			});
		} catch (err) {
			const message = err instanceof Error ? err.message : "Failed to update item";
			updateState({ error: message });
		}
	};

	const handleStartPlacement = (): void => {
		if (state.newItemContent.trim().length === 0) return;
		if (state.newItemContent.trim().length > 500) {
			updateState({ error: "アイテムテキストは500文字以内です" });
			return;
		}
		itemManagerRef.current?.setPlacementMode(true);
		updateState({ isPlacementMode: true, selectedItemId: null });
	};

	const handleCancelPlacement = (): void => {
		itemManagerRef.current?.setPlacementMode(false);
		updateState({ isPlacementMode: false });
	};

	// =========================================================================
	// Render
	// =========================================================================

	if (state.loading) {
		return (
			<div style={styles.container} data-testid="room-editor-loading">
				<p>読み込み中...</p>
			</div>
		);
	}

	if (state.error && !state.room) {
		return (
			<div style={styles.container} data-testid="room-editor-error">
				<p style={styles.errorText}>エラー: {state.error}</p>
			</div>
		);
	}

	return (
		<div style={styles.container} data-testid="room-editor">
			{/* Header */}
			<div style={styles.header}>
				<h2 style={styles.title}>{state.room?.name ?? "Room"}</h2>
				<span style={styles.itemCount}>アイテム: {state.items.length}件</span>
			</div>

			{/* 3D Canvas */}
			<div ref={containerRef} style={styles.canvasContainer}>
				<canvas ref={canvasRef} style={styles.canvas} data-testid="room-canvas" />

				{/* Pointer lock instruction overlay */}
				{!(state.isPointerLocked || state.isPlacementMode) && (
					<div style={styles.overlay} data-testid="pointer-lock-overlay">
						<p>クリックして3D空間を操作</p>
						<p style={styles.overlaySubtext}>WASD: 移動 / マウス: 視点</p>
						<p style={styles.overlaySubtext}>ESC: 操作解除</p>
					</div>
				)}

				{/* Placement mode overlay */}
				{state.isPlacementMode && (
					<div style={styles.placementOverlay} data-testid="placement-overlay">
						<p>床をクリックしてアイテムを配置</p>
						<button type="button" onClick={handleCancelPlacement} style={styles.cancelButton}>
							キャンセル
						</button>
					</div>
				)}
			</div>

			{/* Controls Panel */}
			<div style={styles.panel}>
				{/* Error message */}
				{state.error && <p style={styles.errorText}>{state.error}</p>}

				{/* New item input */}
				<div style={styles.inputGroup}>
					<label htmlFor="new-item-content" style={styles.label}>
						新しいアイテム
					</label>
					<div style={styles.inputRow}>
						<input
							id="new-item-content"
							type="text"
							value={state.newItemContent}
							onChange={(e) => updateState({ newItemContent: e.target.value })}
							placeholder="記憶したいテキスト（1-500文字）"
							maxLength={500}
							style={styles.input}
							data-testid="new-item-input"
						/>
						<button
							type="button"
							onClick={handleStartPlacement}
							disabled={state.newItemContent.trim().length === 0}
							style={{
								...styles.button,
								...(state.newItemContent.trim().length === 0 ? styles.buttonDisabled : {}),
							}}
							data-testid="place-item-button"
						>
							配置
						</button>
					</div>
				</div>

				{/* Selected item controls */}
				{state.selectedItemId && (
					<div style={styles.selectedPanel} data-testid="selected-item-panel">
						<label htmlFor="edit-item-content" style={styles.label}>
							選択中のアイテム
						</label>
						<div style={styles.inputRow}>
							<input
								id="edit-item-content"
								type="text"
								value={state.editContent}
								onChange={(e) => updateState({ editContent: e.target.value })}
								maxLength={500}
								style={styles.input}
								data-testid="edit-item-input"
							/>
							<button
								type="button"
								onClick={handleUpdateItem}
								disabled={state.editContent.trim().length === 0}
								style={styles.button}
								data-testid="update-item-button"
							>
								更新
							</button>
							<button
								type="button"
								onClick={handleDeleteItem}
								style={styles.deleteButton}
								data-testid="delete-item-button"
							>
								削除
							</button>
						</div>
					</div>
				)}

				{/* Items list */}
				<div style={styles.itemsList}>
					<h3 style={styles.itemsListTitle}>配置済みアイテム</h3>
					{state.items.length === 0 ? (
						<p style={styles.emptyText}>アイテムがありません。上のフォームから追加してください。</p>
					) : (
						<ul style={styles.list}>
							{state.items.map((item) => (
								<li
									key={item.id}
									style={{
										...styles.listItem,
										...(item.id === state.selectedItemId ? styles.listItemSelected : {}),
									}}
								>
									<span style={styles.itemText}>{item.content}</span>
									<span style={styles.itemPosition}>
										({item.position_x.toFixed(1)}, {item.position_z.toFixed(1)})
									</span>
								</li>
							))}
						</ul>
					)}
				</div>
			</div>
		</div>
	);
}

// =============================================================================
// Inline styles (MVP — will be replaced by CSS modules or styled-components)
// =============================================================================

const styles = {
	container: {
		display: "flex",
		flexDirection: "column",
		height: "100vh",
		backgroundColor: "#0a0a1a",
		color: "#e0e0e0",
		fontFamily: "system-ui, sans-serif",
	},
	header: {
		display: "flex",
		alignItems: "center",
		justifyContent: "space-between",
		padding: "12px 20px",
		backgroundColor: "#1a1a2e",
		borderBottom: "1px solid #2a2a4a",
	},
	title: {
		margin: 0,
		fontSize: "1.2rem",
		fontWeight: 600,
	},
	itemCount: {
		fontSize: "0.85rem",
		color: "#888",
	},
	canvasContainer: {
		position: "relative",
		flex: 1,
		minHeight: "300px",
	},
	canvas: {
		display: "block",
		width: "100%",
		height: "100%",
	},
	overlay: {
		position: "absolute",
		top: "50%",
		left: "50%",
		transform: "translate(-50%, -50%)",
		textAlign: "center",
		padding: "24px",
		backgroundColor: "rgba(0, 0, 0, 0.7)",
		borderRadius: "12px",
		pointerEvents: "none",
	},
	overlaySubtext: {
		fontSize: "0.85rem",
		color: "#888",
		margin: "4px 0",
	},
	placementOverlay: {
		position: "absolute",
		top: "20px",
		left: "50%",
		transform: "translateX(-50%)",
		textAlign: "center",
		padding: "12px 24px",
		backgroundColor: "rgba(0, 170, 100, 0.85)",
		borderRadius: "8px",
	},
	panel: {
		padding: "16px 20px",
		backgroundColor: "#1a1a2e",
		borderTop: "1px solid #2a2a4a",
		maxHeight: "250px",
		overflowY: "auto",
	},
	inputGroup: {
		marginBottom: "12px",
	},
	inputRow: {
		display: "flex",
		gap: "8px",
	},
	label: {
		display: "block",
		marginBottom: "4px",
		fontSize: "0.85rem",
		color: "#aaa",
	},
	input: {
		flex: 1,
		padding: "8px 12px",
		backgroundColor: "#2a2a4a",
		border: "1px solid #3a3a5c",
		borderRadius: "6px",
		color: "#e0e0e0",
		fontSize: "0.9rem",
		outline: "none",
	},
	button: {
		padding: "8px 16px",
		backgroundColor: "#0066cc",
		color: "#fff",
		border: "none",
		borderRadius: "6px",
		cursor: "pointer",
		fontSize: "0.85rem",
		whiteSpace: "nowrap",
	},
	buttonDisabled: {
		backgroundColor: "#333",
		color: "#666",
		cursor: "not-allowed",
	},
	cancelButton: {
		padding: "6px 14px",
		backgroundColor: "transparent",
		color: "#fff",
		border: "1px solid #fff",
		borderRadius: "6px",
		cursor: "pointer",
		marginTop: "8px",
	},
	deleteButton: {
		padding: "8px 16px",
		backgroundColor: "#cc3333",
		color: "#fff",
		border: "none",
		borderRadius: "6px",
		cursor: "pointer",
		fontSize: "0.85rem",
	},
	selectedPanel: {
		marginBottom: "12px",
		padding: "12px",
		backgroundColor: "#2a2a4a",
		borderRadius: "8px",
		border: "1px solid #ffaa00",
	},
	itemsList: {
		marginTop: "8px",
	},
	itemsListTitle: {
		margin: "0 0 8px",
		fontSize: "0.9rem",
		fontWeight: 600,
	},
	emptyText: {
		fontSize: "0.85rem",
		color: "#666",
	},
	list: {
		listStyle: "none",
		margin: 0,
		padding: 0,
	},
	listItem: {
		display: "flex",
		justifyContent: "space-between",
		alignItems: "center",
		padding: "6px 8px",
		borderRadius: "4px",
		marginBottom: "4px",
		backgroundColor: "#2a2a4a",
	},
	listItemSelected: {
		backgroundColor: "#3a3a5c",
		border: "1px solid #ffaa00",
	},
	itemText: {
		fontSize: "0.85rem",
		overflow: "hidden",
		textOverflow: "ellipsis",
		whiteSpace: "nowrap",
		maxWidth: "70%",
	},
	itemPosition: {
		fontSize: "0.75rem",
		color: "#888",
		whiteSpace: "nowrap",
	},
	errorText: {
		color: "#ff4444",
		fontSize: "0.85rem",
		marginBottom: "8px",
	},
} satisfies Record<string, React.CSSProperties>;
