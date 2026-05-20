/**
 * Переиспользуемые состояния страницы — раньше блоки loading/error
 * были скопированы в каждой странице. Теперь один источник правды.
 */

export function LoadingState() {
  return (
    <div className="px-6 sm:px-11 py-9 max-w-[1100px] mx-auto">
      {/* плейсхолдер заголовка */}
      <div className="h-7 w-52 rounded-lg bg-line animate-pulse mb-7" />
      {/* плейсхолдеры карточек */}
      <div className="flex flex-col gap-3.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-28 rounded-2xl bg-surface border border-line animate-pulse"
          />
        ))}
      </div>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-2 px-6 text-center">
      <div className="font-display text-xl tracking-wide uppercase text-ink">
        Something went wrong
      </div>
      <div className="text-sm text-brand">{message}</div>
    </div>
  );
}
