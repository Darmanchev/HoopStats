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
    <div className="flex flex-col items-center justify-center h-screen bg-bg text-ink">
      <div className="text-[72px] font-black text-brand leading-none">
        {status}
      </div>
      <div className="text-xl mt-2 text-muted">{message}</div>
      <Link
        to="/"
        className="mt-6 px-6 py-2.5 bg-brand text-white rounded-lg no-underline
                   font-semibold hover:opacity-90 transition-opacity"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
