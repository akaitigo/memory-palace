/**
 * Password strength estimation.
 *
 * A deliberately simple length + character-variety heuristic (no external
 * dependency). One point is awarded for each satisfied criterion:
 *   - length >= 8
 *   - contains both lower and upper case letters
 *   - contains a digit
 *   - contains a symbol (non-alphanumeric)
 * The resulting 0-4 score maps to a weak / medium / strong label.
 */

export type PasswordStrength = "weak" | "medium" | "strong";

export interface PasswordStrengthResult {
	/** Number of satisfied criteria, 0-4. */
	score: number;
	/** Human-facing strength bucket. */
	label: PasswordStrength;
}

const MAX_SCORE = 4;

/** Estimate the strength of a password. */
export function getPasswordStrength(password: string): PasswordStrengthResult {
	if (password.length === 0) {
		return { score: 0, label: "weak" };
	}

	let score = 0;
	if (password.length >= 8) {
		score += 1;
	}
	if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {
		score += 1;
	}
	if (/\d/.test(password)) {
		score += 1;
	}
	if (/[^A-Za-z0-9]/.test(password)) {
		score += 1;
	}

	let label: PasswordStrength;
	if (score <= 1) {
		label = "weak";
	} else if (score <= 3) {
		label = "medium";
	} else {
		label = "strong";
	}

	return { score, label };
}

/** Score expressed as a 0-100 percentage, useful for a progress bar width. */
export function passwordStrengthPercent(result: PasswordStrengthResult): number {
	return Math.round((result.score / MAX_SCORE) * 100);
}
