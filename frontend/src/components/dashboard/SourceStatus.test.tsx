import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { retrySync } from "../../lib/api";
import SourceStatus from "./SourceStatus";
vi.mock("../../lib/api", () => ({ retrySync: vi.fn() }));
beforeEach(() => vi.clearAllMocks());
it("shows import groups and retries failed imports without retaining the token", async () => {
 vi.mocked(retrySync).mockResolvedValue({ queued: true });
 render(<SourceStatus statuses={{sync_players:{state:"failed",last_attempt:"2026-10-01",last_success:"2026-09-30"}}} unavailable={false} onQueued={vi.fn()} />);
 for(const label of ["Scores","Player statistics","Predictions"]) expect(screen.getByText(label)).toBeInTheDocument();
 expect(screen.getAllByText(/Update failed/).length).toBeGreaterThan(0);
 await userEvent.type(screen.getByLabelText("Import access token"), "secret");
 await userEvent.click(screen.getByRole("button", {name:/Retry players/}));
 expect(retrySync).toHaveBeenCalledWith("sync_players", "secret");
 expect(screen.getByLabelText("Import access token")).toHaveValue("");
 expect(await screen.findByText(/Retry queued/)).toBeInTheDocument();
});
it("explains unavailable status", () => {
 render(<SourceStatus statuses={{}} unavailable onQueued={vi.fn()} />);
 expect(screen.getByText(/Import status unavailable/)).toBeInTheDocument();
});
it("reports authorization failures without exposing the token", async () => {
 vi.mocked(retrySync).mockRejectedValue({status:403});
 render(<SourceStatus statuses={{sync_players:{state:"failed",last_attempt:"2026-10-01"}}} unavailable={false} onQueued={vi.fn()} />);
 await userEvent.type(screen.getByLabelText("Import access token"), "secret");
 await userEvent.click(screen.getByRole("button", {name:/Retry players/}));
 expect(await screen.findByText(/Retry access denied/)).toBeInTheDocument();
 expect(screen.getByLabelText("Import access token")).toHaveValue("");
});
