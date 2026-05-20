import { Component } from "react";
import type { ReactNode, ErrorInfo } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

/**
 * Ловит ошибки рендера в дочернем дереве и показывает фолбэк
 * вместо белого экрана. Error boundary обязан быть class-компонентом —
 * хуков-аналога getDerivedStateFromError / componentDidCatch нет.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught a render error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen gap-3 px-6 text-center bg-bg">
          <div className="font-display text-2xl tracking-wide uppercase text-ink">
            Something broke
          </div>
          <div className="text-sm text-brand max-w-md break-words">
            {this.state.message}
          </div>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 px-6 py-2.5 bg-brand text-white text-sm font-semibold
                       rounded-lg cursor-pointer border-none hover:opacity-90 transition-opacity"
          >
            Reload page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
