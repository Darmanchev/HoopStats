export const TEAM_COLORS: Record<string, { color: string; accent: string }> = {
  ATL: { color: "#C8102E", accent: "#FDB927" },
  BOS: { color: "#006532", accent: "#9DC535" },
  BKN: { color: "#000000", accent: "#FFFFFF" },
  CHA: { color: "#1D1160", accent: "#00788C" },
  CHI: { color: "#CE1141", accent: "#000000" },
  CLE: { color: "#860038", accent: "#FDBB30" },
  DAL: { color: "#00538C", accent: "#002B5E" },
  DEN: { color: "#0E2240", accent: "#FEC524" },
  DET: { color: "#C8102E", accent: "#1D42BA" },
  GSW: { color: "#1D428A", accent: "#FFC72C" },
  HOU: { color: "#CE1141", accent: "#000000" },
  IND: { color: "#002D62", accent: "#FDBB30" },
  LAC: { color: "#7B1028", accent: "#1168C4" },
  LAL: { color: "#3B1F6B", accent: "#FDB927" },
  MEM: { color: "#5D76A9", accent: "#12173F" },
  MIA: { color: "#8B0022", accent: "#F9A01B" },
  MIL: { color: "#003313", accent: "#A3D55C" },
  MIN: { color: "#0C2340", accent: "#236192" },
  NOP: { color: "#0C2340", accent: "#85714D" },
  NYK: { color: "#005BA1", accent: "#F58426" },
  OKC: { color: "#00599C", accent: "#EF3B24" },
  ORL: { color: "#0077C0", accent: "#C4CED4" },
  PHI: { color: "#006BB6", accent: "#ED174C" },
  PHX: { color: "#1D1160", accent: "#E56020" },
  POR: { color: "#E03A3E", accent: "#000000" },
  SAC: { color: "#5A2D81", accent: "#63727A" },
  SAS: { color: "#C4CED4", accent: "#000000" },
  TOR: { color: "#CE1141", accent: "#000000" },
  UTA: { color: "#002B5C", accent: "#F9A01B" },
  WAS: { color: "#002B5C", accent: "#E31837" },
};

export const DEFAULT_COLOR = { color: "#000000", accent: "#FFFFFF" };

export function getTeamColors(abbr: string | undefined): { color: string; accent: string } {
  if (!abbr) return DEFAULT_COLOR;
  return TEAM_COLORS[abbr.toUpperCase()] || DEFAULT_COLOR;
}
