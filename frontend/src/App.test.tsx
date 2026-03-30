import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
	it("renders the heading", () => {
		render(<App />);
		expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Memory Palace");
	});

	it("renders the description text", () => {
		render(<App />);
		expect(screen.getByText("記憶宮殿 - 間隔反復学習ツール")).toBeDefined();
	});
});
