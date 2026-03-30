/**
 * Statistics Dashboard component.
 *
 * Displays review statistics, daily accuracy charts, room mastery breakdown,
 * and forgetting curve visualization using Recharts.
 */

import { reviewApi } from "@/lib/api";
import type { DailyStatsEntry, ForgettingCurveItem, RoomStatsResponse } from "@/types/api";
import { useCallback, useEffect, useState } from "react";
import {
	CartesianGrid,
	Cell,
	Legend,
	Line,
	LineChart,
	Pie,
	PieChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

export interface StatsDashboardProps {
	roomId: string;
	onBack: () => void;
}

interface DashboardState {
	stats: RoomStatsResponse | null;
	dailyEntries: DailyStatsEntry[];
	forgettingCurves: ForgettingCurveItem[];
	loading: boolean;
	error: string | null;
	dateRange: number;
}

const DATE_RANGE_OPTIONS = [7, 14, 30, 90] as const;

const PIE_COLORS = ["#00cc66", "#ffaa00", "#888888"];

export function StatsDashboard({ roomId, onBack }: StatsDashboardProps): React.JSX.Element {
	const [state, setState] = useState<DashboardState>({
		stats: null,
		dailyEntries: [],
		forgettingCurves: [],
		loading: true,
		error: null,
		dateRange: 30,
	});

	const loadData = useCallback(
		async (days: number) => {
			try {
				setState((prev) => ({ ...prev, loading: true, error: null }));

				const [stats, daily, curves] = await Promise.all([
					reviewApi.getStats(roomId),
					reviewApi.getDailyStats(roomId, days),
					reviewApi.getForgettingCurve(roomId),
				]);

				setState((prev) => ({
					...prev,
					stats,
					dailyEntries: daily.entries,
					forgettingCurves: curves.items,
					loading: false,
					dateRange: days,
				}));
			} catch (err) {
				const message = err instanceof Error ? err.message : "Failed to load statistics";
				setState((prev) => ({ ...prev, error: message, loading: false }));
			}
		},
		[roomId],
	);

	useEffect(() => {
		loadData(state.dateRange);
	}, [loadData, state.dateRange]);

	const handleDateRangeChange = (days: number): void => {
		loadData(days);
	};

	if (state.loading) {
		return (
			<div style={styles.container} data-testid="stats-loading">
				<p style={styles.statusText}>統計データを読み込み中...</p>
			</div>
		);
	}

	if (state.error) {
		return (
			<div style={styles.container} data-testid="stats-error">
				<p style={styles.errorText}>{state.error}</p>
				<button type="button" onClick={onBack} style={styles.backButton}>
					戻る
				</button>
			</div>
		);
	}

	const { stats } = state;

	// Prepare pie chart data
	const masteryData = stats
		? [
				{ name: "定着済み", value: stats.mastered_items },
				{ name: "学習中", value: stats.learning_items },
				{ name: "未学習", value: stats.new_items },
			]
		: [];

	// Filter daily entries with reviews for chart
	const chartData = state.dailyEntries.map((entry) => ({
		date: entry.date.slice(5), // MM-DD format
		review_count: entry.review_count,
		correct_rate: entry.correct_rate ?? 0,
		average_quality: entry.average_quality ?? 0,
	}));

	// Forgetting curve colors
	const curveColors = ["#4488ff", "#ff8844", "#44cc88", "#cc44ff", "#ffcc44"];

	return (
		<div style={styles.container} data-testid="stats-dashboard">
			{/* Header */}
			<div style={styles.header}>
				<button type="button" onClick={onBack} style={styles.backButton} data-testid="stats-back-button">
					← 戻る
				</button>
				<h2 style={styles.title}>統計ダッシュボード</h2>
			</div>

			{/* Summary cards */}
			{stats && (
				<div style={styles.summaryGrid} data-testid="stats-summary">
					<div style={styles.summaryCard}>
						<span style={styles.summaryValue}>{stats.total_items}</span>
						<span style={styles.summaryLabel}>総アイテム数</span>
					</div>
					<div style={styles.summaryCard}>
						<span style={styles.summaryValue}>{stats.total_reviews}</span>
						<span style={styles.summaryLabel}>総復習回数</span>
					</div>
					<div style={styles.summaryCard}>
						<span style={styles.summaryValue}>{stats.reviews_today}</span>
						<span style={styles.summaryLabel}>今日の復習</span>
					</div>
					<div style={styles.summaryCard}>
						<span style={styles.summaryValue}>
							{stats.average_quality !== null ? stats.average_quality.toFixed(1) : "-"}
						</span>
						<span style={styles.summaryLabel}>平均品質</span>
					</div>
				</div>
			)}

			{/* Mastery breakdown */}
			{stats && stats.total_items > 0 && (
				<div style={styles.section} data-testid="mastery-chart">
					<h3 style={styles.sectionTitle}>記憶定着率</h3>
					<div style={styles.chartContainer}>
						<ResponsiveContainer width="100%" height={250}>
							<PieChart>
								<Pie
									data={masteryData}
									cx="50%"
									cy="50%"
									outerRadius={80}
									dataKey="value"
									label={({ name, value }: { name?: string; value?: number }) =>
										value && value > 0 ? `${name ?? ""}: ${value}` : ""
									}
								>
									{masteryData.map((_, index) => (
										<Cell
											key={`cell-${masteryData[index]?.name ?? index}`}
											fill={PIE_COLORS[index % PIE_COLORS.length]}
										/>
									))}
								</Pie>
								<Tooltip />
								<Legend />
							</PieChart>
						</ResponsiveContainer>
					</div>
				</div>
			)}

			{/* Daily review chart */}
			<div style={styles.section} data-testid="daily-chart">
				<div style={styles.sectionHeader}>
					<h3 style={styles.sectionTitle}>日別復習数・正答率</h3>
					<div style={styles.dateRangeButtons}>
						{DATE_RANGE_OPTIONS.map((days) => (
							<button
								key={days}
								type="button"
								onClick={() => handleDateRangeChange(days)}
								style={{
									...styles.rangeButton,
									...(state.dateRange === days ? styles.rangeButtonActive : {}),
								}}
								data-testid={`range-${days}`}
							>
								{days}日
							</button>
						))}
					</div>
				</div>
				<div style={styles.chartContainer}>
					<ResponsiveContainer width="100%" height={300}>
						<LineChart data={chartData}>
							<CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
							<XAxis dataKey="date" stroke="#888" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
							<YAxis yAxisId="left" stroke="#4488ff" tick={{ fontSize: 11 }} />
							<YAxis yAxisId="right" orientation="right" stroke="#00cc66" tick={{ fontSize: 11 }} domain={[0, 100]} />
							<Tooltip contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #2a2a4a", color: "#e0e0e0" }} />
							<Legend />
							<Line
								yAxisId="left"
								type="monotone"
								dataKey="review_count"
								stroke="#4488ff"
								name="復習数"
								dot={false}
								strokeWidth={2}
							/>
							<Line
								yAxisId="right"
								type="monotone"
								dataKey="correct_rate"
								stroke="#00cc66"
								name="正答率(%)"
								dot={false}
								strokeWidth={2}
							/>
						</LineChart>
					</ResponsiveContainer>
				</div>
			</div>

			{/* Forgetting curves */}
			{state.forgettingCurves.length > 0 && (
				<div style={styles.section} data-testid="forgetting-curve-chart">
					<h3 style={styles.sectionTitle}>忘却曲線</h3>
					<p style={styles.sectionDescription}>R(t) = e^(-t/S) — S(安定度) = interval × ease_factor</p>
					<div style={styles.chartContainer}>
						<ResponsiveContainer width="100%" height={300}>
							<LineChart>
								<CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
								<XAxis
									dataKey="days_since_review"
									type="number"
									stroke="#888"
									tick={{ fontSize: 11 }}
									label={{ value: "日数", position: "insideBottomRight", offset: -5, fill: "#888" }}
									domain={["dataMin", "dataMax"]}
								/>
								<YAxis
									stroke="#888"
									tick={{ fontSize: 11 }}
									domain={[0, 1]}
									tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
									label={{ value: "記憶保持率", angle: -90, position: "insideLeft", fill: "#888" }}
								/>
								<Tooltip
									contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #2a2a4a", color: "#e0e0e0" }}
									formatter={(value: unknown) => `${Math.round(Number(value) * 100)}%`}
								/>
								<Legend />
								{state.forgettingCurves.map((item, index) => (
									<Line
										key={item.item_id}
										data={item.curve}
										type="monotone"
										dataKey="retention"
										stroke={curveColors[index % curveColors.length]}
										name={item.content.length > 20 ? `${item.content.slice(0, 17)}...` : item.content}
										dot={false}
										strokeWidth={2}
									/>
								))}
							</LineChart>
						</ResponsiveContainer>
					</div>
				</div>
			)}

			{/* Mobile warning */}
			<div style={styles.mobileWarning} data-testid="mobile-warning">
				<p>3D復習モードはデスクトップでの利用を推奨します。</p>
			</div>
		</div>
	);
}

// =============================================================================
// Inline styles
// =============================================================================

const styles = {
	container: {
		minHeight: "100vh",
		backgroundColor: "#0a0a1a",
		color: "#e0e0e0",
		fontFamily: "system-ui, sans-serif",
		padding: "20px",
	},
	statusText: {
		color: "#888",
		fontSize: "1rem",
		textAlign: "center",
		paddingTop: "40vh",
	},
	errorText: {
		color: "#ff4444",
		fontSize: "1rem",
		textAlign: "center",
		paddingTop: "40vh",
	},
	header: {
		display: "flex",
		alignItems: "center",
		gap: "16px",
		marginBottom: "24px",
		maxWidth: "900px",
		margin: "0 auto 24px auto",
	},
	title: {
		margin: 0,
		fontSize: "1.4rem",
		fontWeight: 600,
	},
	backButton: {
		padding: "6px 12px",
		backgroundColor: "#2a2a4a",
		color: "#e0e0e0",
		border: "1px solid #3a3a5c",
		borderRadius: "6px",
		cursor: "pointer",
		fontSize: "0.85rem",
	},
	summaryGrid: {
		display: "grid",
		gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
		gap: "12px",
		maxWidth: "900px",
		margin: "0 auto 24px auto",
	},
	summaryCard: {
		display: "flex",
		flexDirection: "column",
		alignItems: "center",
		padding: "16px",
		backgroundColor: "#1a1a2e",
		borderRadius: "8px",
		border: "1px solid #2a2a4a",
	},
	summaryValue: {
		fontSize: "1.6rem",
		fontWeight: 700,
		color: "#4488ff",
	},
	summaryLabel: {
		fontSize: "0.8rem",
		color: "#888",
		marginTop: "4px",
	},
	section: {
		maxWidth: "900px",
		margin: "0 auto 32px auto",
		backgroundColor: "#1a1a2e",
		borderRadius: "12px",
		border: "1px solid #2a2a4a",
		padding: "20px",
	},
	sectionHeader: {
		display: "flex",
		justifyContent: "space-between",
		alignItems: "center",
		marginBottom: "16px",
		flexWrap: "wrap",
		gap: "8px",
	},
	sectionTitle: {
		margin: 0,
		fontSize: "1.1rem",
		fontWeight: 600,
	},
	sectionDescription: {
		fontSize: "0.8rem",
		color: "#888",
		marginTop: "4px",
		marginBottom: "16px",
	},
	chartContainer: {
		width: "100%",
		minHeight: "250px",
	},
	dateRangeButtons: {
		display: "flex",
		gap: "6px",
	},
	rangeButton: {
		padding: "4px 10px",
		backgroundColor: "#2a2a4a",
		color: "#aaa",
		border: "1px solid #3a3a5c",
		borderRadius: "4px",
		cursor: "pointer",
		fontSize: "0.8rem",
	},
	rangeButtonActive: {
		backgroundColor: "#0066cc",
		color: "#fff",
		borderColor: "#0066cc",
	},
	mobileWarning: {
		maxWidth: "900px",
		margin: "0 auto",
		textAlign: "center",
		padding: "12px",
		fontSize: "0.8rem",
		color: "#666",
	},
} satisfies Record<string, React.CSSProperties>;
