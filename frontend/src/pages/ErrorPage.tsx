import { useRouteError, Link } from "react-router-dom";

interface RouteError {
  status?: number;
  statusText?: string;
  message?: string;
}

export default function ErrorPage() {
  const error = useRouteError() as RouteError;

  const status = error?.status || 500;
  const message = error?.message || "Something went wrong";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        background: "#F4F6FC",
        color: "#1C2235",
        fontFamily: "'Barlow',sans-serif",
      }}
    >
      <div style={{ fontSize: 72, fontWeight: 900, color: "oklch(0.62 0.18 25)" }}>
        {status}
      </div>
      <div style={{ fontSize: 20, marginTop: 8, color: "#6B7590" }}>
        {message}
      </div>
      <Link
        to="/"
        style={{
          marginTop: 24,
          padding: "10px 24px",
          background: "oklch(0.62 0.18 25)",
          color: "#fff",
          borderRadius: 8,
          textDecoration: "none",
          fontWeight: 600,
        }}
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
