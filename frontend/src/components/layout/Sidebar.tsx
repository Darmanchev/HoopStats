import { NavLink } from "react-router-dom";

const nav = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
    to: "/",
  },
  {
    id: "schedule",
    label: "Schedule",
    icon: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 002 2v12a2 2 0 002 2z",
    to: "/schedule",
  },
  {
    id: "teams",
    label: "Teams",
    icon: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2",
    to: "/teams",
  },
  {
    id: "players",
    label: "Players",
    icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
    to: "/players",
  },
  {
    id: "injuries",
    label: "Injuries",
    icon: "M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    to: "/injuries",
  },
];

const soon = ["Analytics"];

export default function Sidebar() {
  return (
    <div
      style={{
        width: 218,
        background: "#FAFBFF",
        borderRight: "1px solid #181E2C",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
        overflow: "hidden",
        boxSizing: "border-box",
      }}
    >
      <div style={{ padding: "26px 22px", borderBottom: "1px solid #181E2C" }}>
        <div
          style={{
            fontFamily: "'Barlow Condensed',sans-serif",
            fontWeight: 900,
            fontSize: 22,
            letterSpacing: 2.5,
            textTransform: "uppercase",
          }}
        >
          Hoop<span style={{ color: "oklch(0.62 0.18 25)" }}>Stats</span>
        </div>
        <div
          style={{
            fontSize: 10,
            letterSpacing: 1.8,
            color: "#8A94AE",
            marginTop: 3,
          }}
        >
          NBA ANALYTICS
        </div>
      </div>

      <nav style={{ padding: "14px 10px", flex: 1 }}>
        {nav.map((item) => (
          <NavLink
            key={item.id}
            to={item.to}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: 10,
              width: "100%",
              padding: "10px 12px",
              borderRadius: 8,
              marginBottom: 3,
              background: isActive ? "oklch(0.90 0.04 220)" : "transparent",
              border: `1px solid ${isActive ? "oklch(0.75 0.06 220)" : "transparent"}`,
              color: isActive ? "#1C2235" : "#6B7590",
              cursor: "pointer",
              fontFamily: "'Barlow',sans-serif",
              fontWeight: 500,
              fontSize: 14,
              textAlign: "left",
              transition: "all 0.12s",
              textDecoration: "none",
              boxSizing: "border-box",
            })}
          >
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d={item.icon} />
            </svg>
            {item.label}
          </NavLink>
        ))}

        <div style={{ height: 1, background: "#EDF0F8", margin: "12px 4px" }} />

        {soon.map((label) => (
          <div
            key={label}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 12px",
              borderRadius: 8,
              marginBottom: 3,
              color: "#BDC4D6",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 15,
                  height: 15,
                  background: "#EDF0F8",
                  borderRadius: 3,
                  flexShrink: 0,
                }}
              />
              <span style={{ fontFamily: "'Barlow',sans-serif", fontSize: 14 }}>
                {label}
              </span>
            </div>
            <span
              style={{
                fontSize: 9,
                letterSpacing: 1.2,
                color: "#E4E8F2",
                fontWeight: 700,
              }}
            >
              SOON
            </span>
          </div>
        ))}
      </nav>

      <div style={{ padding: "16px 22px", borderTop: "1px solid #181E2C" }}>
        <div
          style={{
            fontSize: 10,
            letterSpacing: 1.4,
            color: "#BDC4D6",
            fontWeight: 700,
            marginBottom: 4,
          }}
        >
          2025–26 SEASON
        </div>
        <div style={{ fontSize: 12, color: "#8A94AE" }}>Playoffs · Round 1</div>
      </div>
    </div>
  );
}
