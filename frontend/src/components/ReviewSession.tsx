/**
 * Review Session component.
 *
 * Guides the user through reviewing memory items in a 3D room.
 * Shows items one-by-one, animates camera to each item position,
 * and collects quality self-assessment (0-5).
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { reviewApi } from "@/lib/api";
import type { MemoryItem } from "@/types/api";

export interface ReviewSessionProps {
	roomId: string;
	onComplete: () => void;
	onBack: () => void;
}

interface ReviewState {
	queue: MemoryItem[];
	currentIndex: number;
	loading: boolean;
	error: string | null;
	showContent: boolean;
	startTime: number;
	completed: boolean;
	results: Array<{ itemId: string; quality: number }>;
}

const QUALITY_LABELS: Record<number, string> = {
	0: "完全忘却",
	1: "不正解（見れば分かる）",
	2: "不正解（簡単に思い出せそう）",
	3: "正解（かなり困難）",
	4: "正解（少し迷った）",
	5: "完璧（即座に想起）",
};

export function ReviewSession({ roomId, onComplete, onBack }: ReviewSessionProps): React.JSX.Element {
	const [state, setState] = useState<ReviewState>({
		queue: [],
		currentIndex: 0,
		loading: true,
		error: null,
		showContent: false,
		startTime: Date.now(),
		completed: false,
		results: [],
	});

	const startTimeRef = useRef(Date.now());

	const loadQueue = useCallback(async () => {
		try {
			setState((prev) => ({ ...prev, loading: true, error: null }));
			const queue = await reviewApi.getQueue(roomId);
			setState((prev) => ({
				...prev,
				queue,
				loading: false,
				currentIndex: 0,
				completed: queue.length === 0,
			}));
			startTimeRef.current = Date.now();
		} catch (err) {
			const message = err instanceof Error ? err.message : "Failed to load review queue";
			setState((prev) => ({ ...prev, error: message, loading: false }));
		}
	}, [roomId]);

	useEffect(() => {
		loadQueue();
	}, [loadQueue]);

	const currentItem: MemoryItem | undefined = state.queue[state.currentIndex];

	const handleShowContent = (): void => {
		setState((prev) => ({ ...prev, showContent: true }));
	};

	const handleQualitySelect = async (quality: number): Promise<void> => {
		if (!currentItem) return;

		const responseTimeMs = Math.min(Date.now() - startTimeRef.current, 300000);

		try {
			await reviewApi.recordReview(roomId, {
				memory_item_id: currentItem.id,
				quality,
				response_time_ms: Math.max(1, responseTimeMs),
			});

			const newResults = [...state.results, { itemId: currentItem.id, quality }];
			const nextIndex = state.currentIndex + 1;
			const isComplete = nextIndex >= state.queue.length;

			setState((prev) => ({
				...prev,
				results: newResults,
				currentIndex: nextIndex,
				showContent: false,
				completed: isComplete,
			}));

			startTimeRef.current = Date.now();
		} catch (err) {
			const message = err instanceof Error ? err.message : "Failed to record review";
			setState((prev) => ({ ...prev, error: message }));
		}
	};

	// Loading state
	if (state.loading) {
		return (
			<div style={styles.container} data-testid="review-loading">
				<p style={styles.statusText}>復習キューを読み込み中...</p>
			</div>
		);
	}

	// Error state
	if (state.error) {
		return (
			<div style={styles.container} data-testid="review-error">
				<p style={styles.errorText}>{state.error}</p>
				<button type="button" onClick={onBack} style={styles.backButton}>
					戻る
				</button>
			</div>
		);
	}

	// Empty queue
	if (state.queue.length === 0) {
		return (
			<div style={styles.container} data-testid="review-empty">
				<div style={styles.emptyState}>
					<h2 style={styles.emptyTitle}>復習するアイテムがありません</h2>
					<p style={styles.emptyDescription}>全てのアイテムが復習済みです。次の復習日まで待ちましょう。</p>
					<button type="button" onClick={onBack} style={styles.backButton} data-testid="review-back-button">
						戻る
					</button>
				</div>
			</div>
		);
	}

	// Completed state
	if (state.completed) {
		const totalItems = state.results.length;
		const correctItems = state.results.filter((r) => r.quality >= 3).length;
		const correctRate = totalItems > 0 ? Math.round((correctItems / totalItems) * 100) : 0;

		return (
			<div style={styles.container} data-testid="review-complete">
				<div style={styles.completeCard}>
					<h2 style={styles.completeTitle}>復習完了</h2>
					<div style={styles.statsGrid}>
						<div style={styles.statItem}>
							<span style={styles.statValue}>{totalItems}</span>
							<span style={styles.statLabel}>復習数</span>
						</div>
						<div style={styles.statItem}>
							<span style={styles.statValue}>{correctRate}%</span>
							<span style={styles.statLabel}>正答率</span>
						</div>
						<div style={styles.statItem}>
							<span style={styles.statValue}>
								{correctItems}/{totalItems}
							</span>
							<span style={styles.statLabel}>正解数</span>
						</div>
					</div>
					<div style={styles.buttonRow}>
						<button type="button" onClick={onComplete} style={styles.primaryButton} data-testid="view-stats-button">
							統計を見る
						</button>
						<button type="button" onClick={onBack} style={styles.backButton} data-testid="review-back-button">
							ルーム一覧に戻る
						</button>
					</div>
				</div>
			</div>
		);
	}

	// Active review
	return (
		<div style={styles.container} data-testid="review-active">
			{/* Progress bar */}
			<div style={styles.progressContainer}>
				<div
					style={{
						...styles.progressBar,
						width: `${(state.currentIndex / state.queue.length) * 100}%`,
					}}
				/>
			</div>
			<div style={styles.progressText}>
				{state.currentIndex + 1} / {state.queue.length}
			</div>

			{/* Item card */}
			<div style={styles.reviewCard} data-testid="review-card">
				{/* Item position indicator */}
				<div style={styles.positionBadge}>
					位置: ({currentItem?.position_x.toFixed(1)}, {currentItem?.position_z.toFixed(1)})
				</div>

				{/* Content area */}
				{!state.showContent ? (
					<div style={styles.contentHidden}>
						<p style={styles.hintText}>このアイテムの内容を思い出してください</p>
						<button
							type="button"
							onClick={handleShowContent}
							style={styles.showButton}
							data-testid="show-content-button"
						>
							答えを見る
						</button>
					</div>
				) : (
					<div style={styles.contentRevealed} data-testid="revealed-content">
						<p style={styles.contentText}>{currentItem?.content}</p>

						{/* Quality buttons */}
						<div style={styles.qualityContainer}>
							<p style={styles.qualityPrompt}>どの程度思い出せましたか？</p>
							<div style={styles.qualityGrid}>
								{([0, 1, 2, 3, 4, 5] as const).map((q) => (
									<button
										key={q}
										type="button"
										onClick={() => handleQualitySelect(q)}
										style={{
											...styles.qualityButton,
											backgroundColor: q >= 3 ? "#1a4a2e" : "#4a1a1a",
											borderColor: q >= 3 ? "#2a8a4a" : "#8a2a2a",
										}}
										data-testid={`quality-button-${q}`}
									>
										<span style={styles.qualityScore}>{q}</span>
										<span style={styles.qualityLabel}>{QUALITY_LABELS[q]}</span>
									</button>
								))}
							</div>
						</div>
					</div>
				)}
			</div>

			{/* Back button */}
			<button type="button" onClick={onBack} style={styles.backButtonSmall} data-testid="review-back-button">
				中断して戻る
			</button>
		</div>
	);
}

// =============================================================================
// Inline styles
// =============================================================================

const styles = {
	container: {
		display: "flex",
		flexDirection: "column",
		alignItems: "center",
		justifyContent: "center",
		minHeight: "100vh",
		backgroundColor: "#0a0a1a",
		color: "#e0e0e0",
		fontFamily: "system-ui, sans-serif",
		padding: "20px",
	},
	statusText: {
		color: "#888",
		fontSize: "1rem",
	},
	errorText: {
		color: "#ff4444",
		fontSize: "1rem",
		marginBottom: "16px",
	},
	emptyState: {
		textAlign: "center",
		maxWidth: "400px",
	},
	emptyTitle: {
		fontSize: "1.4rem",
		marginBottom: "12px",
	},
	emptyDescription: {
		color: "#888",
		fontSize: "0.95rem",
		marginBottom: "24px",
	},
	progressContainer: {
		width: "100%",
		maxWidth: "600px",
		height: "6px",
		backgroundColor: "#2a2a4a",
		borderRadius: "3px",
		overflow: "hidden",
		marginBottom: "8px",
	},
	progressBar: {
		height: "100%",
		backgroundColor: "#0066cc",
		borderRadius: "3px",
		transition: "width 0.3s ease",
	},
	progressText: {
		fontSize: "0.85rem",
		color: "#888",
		marginBottom: "24px",
	},
	reviewCard: {
		width: "100%",
		maxWidth: "600px",
		backgroundColor: "#1a1a2e",
		borderRadius: "12px",
		border: "1px solid #2a2a4a",
		padding: "24px",
		marginBottom: "16px",
	},
	positionBadge: {
		fontSize: "0.75rem",
		color: "#666",
		marginBottom: "16px",
	},
	contentHidden: {
		textAlign: "center",
		padding: "32px 0",
	},
	hintText: {
		fontSize: "1.1rem",
		color: "#aaa",
		marginBottom: "24px",
	},
	showButton: {
		padding: "12px 32px",
		backgroundColor: "#0066cc",
		color: "#fff",
		border: "none",
		borderRadius: "8px",
		cursor: "pointer",
		fontSize: "1rem",
	},
	contentRevealed: {
		textAlign: "center",
	},
	contentText: {
		fontSize: "1.3rem",
		fontWeight: 600,
		marginBottom: "24px",
		lineHeight: 1.5,
		wordBreak: "break-word",
	},
	qualityContainer: {
		borderTop: "1px solid #2a2a4a",
		paddingTop: "16px",
	},
	qualityPrompt: {
		fontSize: "0.9rem",
		color: "#aaa",
		marginBottom: "12px",
	},
	qualityGrid: {
		display: "grid",
		gridTemplateColumns: "repeat(3, 1fr)",
		gap: "8px",
	},
	qualityButton: {
		display: "flex",
		flexDirection: "column",
		alignItems: "center",
		padding: "10px 6px",
		border: "1px solid",
		borderRadius: "8px",
		cursor: "pointer",
		color: "#e0e0e0",
		transition: "opacity 0.15s",
	},
	qualityScore: {
		fontSize: "1.2rem",
		fontWeight: 700,
		marginBottom: "4px",
	},
	qualityLabel: {
		fontSize: "0.7rem",
		color: "#bbb",
		lineHeight: 1.2,
	},
	completeCard: {
		textAlign: "center",
		maxWidth: "500px",
		backgroundColor: "#1a1a2e",
		borderRadius: "12px",
		border: "1px solid #2a2a4a",
		padding: "32px",
	},
	completeTitle: {
		fontSize: "1.5rem",
		marginBottom: "24px",
	},
	statsGrid: {
		display: "flex",
		justifyContent: "center",
		gap: "32px",
		marginBottom: "32px",
	},
	statItem: {
		display: "flex",
		flexDirection: "column",
		alignItems: "center",
	},
	statValue: {
		fontSize: "1.8rem",
		fontWeight: 700,
		color: "#4488ff",
	},
	statLabel: {
		fontSize: "0.8rem",
		color: "#888",
		marginTop: "4px",
	},
	buttonRow: {
		display: "flex",
		gap: "12px",
		justifyContent: "center",
	},
	primaryButton: {
		padding: "12px 24px",
		backgroundColor: "#0066cc",
		color: "#fff",
		border: "none",
		borderRadius: "8px",
		cursor: "pointer",
		fontSize: "0.95rem",
	},
	backButton: {
		padding: "12px 24px",
		backgroundColor: "#2a2a4a",
		color: "#e0e0e0",
		border: "1px solid #3a3a5c",
		borderRadius: "8px",
		cursor: "pointer",
		fontSize: "0.95rem",
	},
	backButtonSmall: {
		padding: "8px 16px",
		backgroundColor: "transparent",
		color: "#888",
		border: "1px solid #3a3a5c",
		borderRadius: "6px",
		cursor: "pointer",
		fontSize: "0.85rem",
	},
} satisfies Record<string, React.CSSProperties>;
