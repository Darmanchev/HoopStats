import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import PlayerHeadshot from "./PlayerHeadshot";

describe("Player headshots", () => {
  it("loads an official image and falls back when it fails", () => {
    render(<PlayerHeadshot nbaId={201939} name="Stephen Curry" />);
    const image = screen.getByRole("img", { name: "Stephen Curry" });
    expect(image).toHaveAttribute("src", "https://cdn.nba.com/headshots/nba/latest/1040x760/201939.png");
    fireEvent.error(image);
    expect(screen.queryByRole("img", { name: "Stephen Curry" })).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Stephen Curry photo unavailable" })).toHaveTextContent("SC");
  });
  it("never builds an image URL from a missing ID", () => {
    render(<PlayerHeadshot nbaId={null} name="Unknown Player" />);
    expect(screen.getByRole("img", { name: "Unknown Player photo unavailable" })).toHaveTextContent("UP");
    expect(screen.queryByAltText("Unknown Player")).not.toBeInTheDocument();
  });
});
