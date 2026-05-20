import { useState, useEffect } from "react";

type Theme = "light" | "dark";

/** Начальная тема: localStorage → системная настройка. */
function getInitialTheme(): Theme {
  try {
    const saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* localStorage недоступен — игнорируем */
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

/**
 * Управляет темой: хранит выбор в localStorage и вешает класс `dark`
 * на <html>. Тема глобальна (через класс на documentElement), поэтому
 * хук достаточно вызвать в одном месте — в ThemeToggle.
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* игнорируем недоступный localStorage */
    }
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return { theme, toggle };
}
