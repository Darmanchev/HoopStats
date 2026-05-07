import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App"; // без изменений, просто проверь

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
