import { useCallback, useEffect, useState } from "react";
import { ReviewSession } from "@/components/ReviewSession";
import { RoomEditor } from "@/components/RoomEditor";
import { StatsDashboard } from "@/components/StatsDashboard";
import { roomApi } from "@/lib/api";
import type { Room, RoomCreateRequest } from "@/types/api";

type View =
	| { type: "list" }
	| { type: "editor"; roomId: string }
	| { type: "review"; roomId: string }
	| { type: "stats"; roomId: string };

export function App(): React.JSX.Element {
	const [view, setView] = useState<View>({ type: "list" });
	const [rooms, setRooms] = useState<Room[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [newRoomName, setNewRoomName] = useState("");

	const loadRooms = useCallback(async () => {
		try {
			setLoading(true);
			setError(null);
			const data = await roomApi.list();
			setRooms(data);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to load rooms");
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		loadRooms();
	}, [loadRooms]);

	const handleCreateRoom = async (): Promise<void> => {
		const name = newRoomName.trim();
		if (name.length === 0 || name.length > 100) return;

		try {
			const body: RoomCreateRequest = { name };
			const room = await roomApi.create(body);
			setRooms((prev) => [room, ...prev]);
			setNewRoomName("");
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to create room");
		}
	};

	const handleDeleteRoom = async (roomId: string): Promise<void> => {
		try {
			await roomApi.delete(roomId);
			setRooms((prev) => prev.filter((r) => r.id !== roomId));
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to delete room");
		}
	};

	if (view.type === "review") {
		return (
			<ReviewSession
				roomId={view.roomId}
				onComplete={() => setView({ type: "stats", roomId: view.roomId })}
				onBack={() => {
					setView({ type: "list" });
					loadRooms();
				}}
			/>
		);
	}

	if (view.type === "stats") {
		return (
			<StatsDashboard
				roomId={view.roomId}
				onBack={() => {
					setView({ type: "list" });
					loadRooms();
				}}
			/>
		);
	}

	if (view.type === "editor") {
		return (
			<div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
				<div
					style={{
						padding: "8px 16px",
						backgroundColor: "#0a0a1a",
						borderBottom: "1px solid #2a2a4a",
					}}
				>
					<button
						type="button"
						onClick={() => {
							setView({ type: "list" });
							loadRooms();
						}}
						style={{
							padding: "6px 12px",
							backgroundColor: "#2a2a4a",
							color: "#e0e0e0",
							border: "1px solid #3a3a5c",
							borderRadius: "6px",
							cursor: "pointer",
							fontSize: "0.85rem",
						}}
						data-testid="back-to-list"
					>
						← ルーム一覧に戻る
					</button>
				</div>
				<div style={{ flex: 1, overflow: "hidden" }}>
					<RoomEditor roomId={view.roomId} />
				</div>
			</div>
		);
	}

	return (
		<div
			style={{
				minHeight: "100vh",
				backgroundColor: "#0a0a1a",
				color: "#e0e0e0",
				fontFamily: "system-ui, sans-serif",
				padding: "40px 20px",
			}}
		>
			<div style={{ maxWidth: "600px", margin: "0 auto" }}>
				<h1 style={{ fontSize: "1.8rem", marginBottom: "8px" }}>Memory Palace</h1>
				<p style={{ color: "#888", marginBottom: "32px" }}>記憶宮殿 - 間隔反復学習ツール</p>

				{/* Error */}
				{error && (
					<p style={{ color: "#ff4444", marginBottom: "16px" }} data-testid="error-message">
						{error}
					</p>
				)}

				{/* Create room */}
				<div style={{ marginBottom: "24px" }}>
					<label
						htmlFor="room-name-input"
						style={{ display: "block", marginBottom: "6px", fontSize: "0.9rem", color: "#aaa" }}
					>
						新しいルームを作成
					</label>
					<div style={{ display: "flex", gap: "8px" }}>
						<input
							id="room-name-input"
							type="text"
							value={newRoomName}
							onChange={(e) => setNewRoomName(e.target.value)}
							placeholder="ルーム名（1-100文字）"
							maxLength={100}
							style={{
								flex: 1,
								padding: "10px 14px",
								backgroundColor: "#1a1a2e",
								border: "1px solid #3a3a5c",
								borderRadius: "8px",
								color: "#e0e0e0",
								fontSize: "0.95rem",
								outline: "none",
							}}
							data-testid="room-name-input"
						/>
						<button
							type="button"
							onClick={handleCreateRoom}
							disabled={newRoomName.trim().length === 0}
							style={{
								padding: "10px 20px",
								backgroundColor: newRoomName.trim().length > 0 ? "#0066cc" : "#333",
								color: newRoomName.trim().length > 0 ? "#fff" : "#666",
								border: "none",
								borderRadius: "8px",
								cursor: newRoomName.trim().length > 0 ? "pointer" : "not-allowed",
								fontSize: "0.9rem",
								whiteSpace: "nowrap",
							}}
							data-testid="create-room-button"
						>
							作成
						</button>
					</div>
				</div>

				{/* Room list */}
				<h2 style={{ fontSize: "1.1rem", marginBottom: "12px" }}>ルーム一覧</h2>

				{loading ? (
					<p style={{ color: "#888" }}>読み込み中...</p>
				) : rooms.length === 0 ? (
					<p style={{ color: "#666" }} data-testid="no-rooms-message">
						ルームがありません。上のフォームから作成してください。
					</p>
				) : (
					<ul style={{ listStyle: "none", padding: 0, margin: 0 }} data-testid="room-list">
						{rooms.map((room) => (
							<li
								key={room.id}
								style={{
									display: "flex",
									justifyContent: "space-between",
									alignItems: "center",
									padding: "12px 16px",
									marginBottom: "8px",
									backgroundColor: "#1a1a2e",
									borderRadius: "8px",
									border: "1px solid #2a2a4a",
								}}
							>
								<button
									type="button"
									onClick={() => setView({ type: "editor", roomId: room.id })}
									style={{
										background: "none",
										border: "none",
										color: "#4488ff",
										cursor: "pointer",
										fontSize: "1rem",
										textAlign: "left",
										flex: 1,
										padding: 0,
									}}
									data-testid={`room-link-${room.id}`}
								>
									{room.name}
								</button>
								<div style={{ display: "flex", gap: "6px" }}>
									<button
										type="button"
										onClick={() => setView({ type: "review", roomId: room.id })}
										style={{
											padding: "4px 10px",
											backgroundColor: "#1a4a2e",
											color: "#44cc88",
											border: "1px solid #2a8a4a",
											borderRadius: "4px",
											cursor: "pointer",
											fontSize: "0.8rem",
										}}
										data-testid={`review-room-${room.id}`}
									>
										復習
									</button>
									<button
										type="button"
										onClick={() => setView({ type: "stats", roomId: room.id })}
										style={{
											padding: "4px 10px",
											backgroundColor: "#1a2a4a",
											color: "#4488ff",
											border: "1px solid #2a4a8a",
											borderRadius: "4px",
											cursor: "pointer",
											fontSize: "0.8rem",
										}}
										data-testid={`stats-room-${room.id}`}
									>
										統計
									</button>
									<button
										type="button"
										onClick={() => handleDeleteRoom(room.id)}
										style={{
											padding: "4px 10px",
											backgroundColor: "transparent",
											color: "#cc3333",
											border: "1px solid #cc3333",
											borderRadius: "4px",
											cursor: "pointer",
											fontSize: "0.8rem",
										}}
										data-testid={`delete-room-${room.id}`}
									>
										削除
									</button>
								</div>
							</li>
						))}
					</ul>
				)}
			</div>
		</div>
	);
}
