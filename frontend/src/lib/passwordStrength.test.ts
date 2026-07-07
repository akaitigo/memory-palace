import { describe, expect, it } from "vitest";
import { getPasswordStrength, passwordStrengthPercent } from "./passwordStrength";

describe("getPasswordStrength", () => {
	it("returns weak with score 0 for an empty password", () => {
		const result = getPasswordStrength("");
		expect(result.score).toBe(0);
		expect(result.label).toBe("weak");
	});

	it("rates a short simple password as weak", () => {
		// Only the lower/upper criterion is met (length < 8, no digit/symbol).
		const result = getPasswordStrength("Abc");
		expect(result.score).toBe(1);
		expect(result.label).toBe("weak");
	});

	it("rates a medium password", () => {
		// length >= 8 + digit = score 2.
		const result = getPasswordStrength("password1");
		expect(result.score).toBe(2);
		expect(result.label).toBe("medium");
	});

	it("rates a strong password meeting all criteria", () => {
		// length >= 8 + mixed case + digit + symbol = score 4.
		const result = getPasswordStrength("Str0ng!Pass");
		expect(result.score).toBe(4);
		expect(result.label).toBe("strong");
	});

	it("does not exceed a score of 4", () => {
		const result = getPasswordStrength("A_very-Str0ng!Password#2026");
		expect(result.score).toBe(4);
		expect(result.label).toBe("strong");
	});
});

describe("passwordStrengthPercent", () => {
	it("maps score to a 0-100 percentage", () => {
		expect(passwordStrengthPercent({ score: 0, label: "weak" })).toBe(0);
		expect(passwordStrengthPercent({ score: 2, label: "medium" })).toBe(50);
		expect(passwordStrengthPercent({ score: 4, label: "strong" })).toBe(100);
	});
});
