import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';

interface ResizableSplitProps {
  left: ReactNode;
  right: ReactNode;
  /** Initial left panel width as percentage (0–100). */
  defaultLeftPct?: number;
  minLeftPx?: number;
  minRightPx?: number;
  storageKey?: string;
  className?: string;
}

function readPct(key: string, fallback: number): number {
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      const n = parseFloat(stored);
      if (n >= 15 && n <= 85) return n;
    }
  } catch {
    /* ignore */
  }
  return fallback;
}

export function ResizableSplit({
  left,
  right,
  defaultLeftPct = 58,
  minLeftPx = 280,
  minRightPx = 240,
  storageKey = 'codenda-panel-split',
  className = '',
}: ResizableSplitProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [leftPct, setLeftPct] = useState(() => readPct(storageKey, defaultLeftPct));
  const dragging = useRef(false);
  const pctRef = useRef(leftPct);

  pctRef.current = leftPct;

  const clampPct = useCallback(
    (pct: number, width: number) => {
      const minL = (minLeftPx / width) * 100;
      const maxL = 100 - (minRightPx / width) * 100;
      return Math.min(maxL, Math.max(minL, pct));
    },
    [minLeftPx, minRightPx],
  );

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const pct = clampPct(((e.clientX - rect.left) / rect.width) * 100, rect.width);
      setLeftPct(pct);
    };

    const onUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      try {
        localStorage.setItem(storageKey, String(pctRef.current));
      } catch {
        /* ignore */
      }
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
  }, [clampPct, storageKey]);

  const startDrag = (e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  return (
    <div ref={containerRef} className={`flex min-h-0 min-w-0 ${className}`}>
      <div className="min-h-0 min-w-0" style={{ flex: `0 0 ${leftPct}%` }}>
        {left}
      </div>

      <div
        role="separator"
        aria-orientation="vertical"
        aria-valuenow={Math.round(leftPct)}
        aria-valuemin={15}
        aria-valuemax={85}
        tabIndex={0}
        onMouseDown={startDrag}
        onKeyDown={(e) => {
          const step = e.shiftKey ? 5 : 2;
          if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            e.preventDefault();
            const delta = e.key === 'ArrowLeft' ? -step : step;
            const width = containerRef.current?.getBoundingClientRect().width ?? 800;
            setLeftPct((p) => clampPct(p + delta, width));
          }
        }}
        className="group relative z-10 w-2 shrink-0 cursor-col-resize touch-none select-none"
      >
        <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-border transition-colors group-hover:bg-brand group-active:bg-brand" />
        <div className="absolute inset-y-0 left-1/2 flex w-4 -translate-x-1/2 items-center justify-center opacity-0 transition-opacity group-hover:opacity-100">
          <div className="h-8 w-1 rounded-full bg-brand/60" />
        </div>
      </div>

      <div className="min-h-0 min-w-0 flex-1">{right}</div>
    </div>
  );
}
