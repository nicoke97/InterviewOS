import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';

function timerTone(elapsed: number, standardSeconds: number): 'ok' | 'warn' | 'over' {
  if (standardSeconds <= 0) return 'ok';
  const ratio = elapsed / standardSeconds;
  if (ratio > 1) return 'over';
  if (ratio >= 0.75) return 'warn';
  return 'ok';
}

const TONE_CLASS: Record<ReturnType<typeof timerTone>, string> = {
  ok: 'text-emerald-700',
  warn: 'text-amber-600',
  over: 'text-red-600',
};

interface SessionTimerProps {
  running: boolean;
  seconds: number;
  standardSeconds: number;
  onTick: () => void;
}

export function SessionTimer({ running, seconds, standardSeconds, onTick }: SessionTimerProps) {
  const ref = useRef<ReturnType<typeof setInterval> | null>(null);
  const onTickRef = useRef(onTick);
  onTickRef.current = onTick;

  useEffect(() => {
    if (ref.current) clearInterval(ref.current);
    ref.current = null;
    if (!running) return undefined;
    ref.current = setInterval(() => {
      onTickRef.current();
    }, 1000);
    return () => {
      if (ref.current) clearInterval(ref.current);
    };
  }, [running]);

  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  const tone = timerTone(seconds, standardSeconds);

  return (
    <span className={`font-mono tabular-nums ${TONE_CLASS[tone]}`}>
      {String(m).padStart(2, '0')}:{String(s).padStart(2, '0')}
    </span>
  );
}

/** @deprecated use SessionTimer */
export function Timer({ running, onTick }: { running: boolean; onTick?: (seconds: number) => void }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!running) setSeconds(0);
  }, [running]);
  return (
    <SessionTimer
      running={running}
      seconds={seconds}
      standardSeconds={0}
      onTick={() => {
        setSeconds((s) => {
          const next = s + 1;
          onTick?.(next);
          return next;
        });
      }}
    />
  );
}

export function useSessionTimer(slot: string) {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const secondsRef = useRef(0);
  const sessionIdRef = useRef<number | null>(null);

  const setElapsed = useCallback((value: number) => {
    secondsRef.current = value;
    setSeconds(value);
  }, []);

  const onTick = useCallback(() => {
    setSeconds((s) => {
      const next = s + 1;
      secondsRef.current = next;
      return next;
    });
  }, []);

  const start = useCallback(async (fromSeconds = 0) => {
    const res = await api.sessionStart(slot);
    setSessionId(res.session_id);
    sessionIdRef.current = res.session_id;
    secondsRef.current = fromSeconds;
    setSeconds(fromSeconds);
    setRunning(true);
  }, [slot]);

  const stop = useCallback(async () => {
    const id = sessionIdRef.current;
    const secs = secondsRef.current;
    sessionIdRef.current = null;
    setRunning(false);
    setSessionId(null);
    if (id) {
      void api.sessionEnd(id, secs).catch(() => {});
    }
  }, []);

  return { running, start, stop, onTick, seconds, setElapsed, secondsRef, sessionId };
}
