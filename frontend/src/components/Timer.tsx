import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';

interface TimerProps {
  running: boolean;
  onTick?: (seconds: number) => void;
}

export function Timer({ running, onTick }: TimerProps) {
  const [seconds, setSeconds] = useState(0);
  const ref = useRef<ReturnType<typeof setInterval> | null>(null);
  const onTickRef = useRef(onTick);
  onTickRef.current = onTick;

  useEffect(() => {
    if (running) {
      setSeconds(0);
      ref.current = setInterval(() => {
        setSeconds((s) => {
          const next = s + 1;
          onTickRef.current?.(next);
          return next;
        });
      }, 1000);
    }
    return () => {
      if (ref.current) clearInterval(ref.current);
    };
  }, [running]);

  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return (
    <span className="font-mono tabular-nums">
      {String(m).padStart(2, '0')}:{String(s).padStart(2, '0')}
    </span>
  );
}

export function useSessionTimer(slot: string) {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const secondsRef = useRef(0);
  const sessionIdRef = useRef<number | null>(null);

  const start = useCallback(async () => {
    const res = await api.sessionStart(slot);
    setSessionId(res.session_id);
    sessionIdRef.current = res.session_id;
    setRunning(true);
    secondsRef.current = 0;
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

  const onTick = useCallback((s: number) => {
    secondsRef.current = s;
  }, []);

  return { running, start, stop, onTick, seconds: secondsRef, sessionId };
}
