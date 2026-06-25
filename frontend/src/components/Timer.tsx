import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';

interface TimerProps {
  running: boolean;
  onTick?: (seconds: number) => void;
}

export function Timer({ running, onTick }: TimerProps) {
  const [seconds, setSeconds] = useState(0);
  const ref = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (running) {
      ref.current = setInterval(() => {
        setSeconds((s) => {
          const next = s + 1;
          onTick?.(next);
          return next;
        });
      }, 1000);
    }
    return () => {
      if (ref.current) clearInterval(ref.current);
    };
  }, [running, onTick]);

  useEffect(() => {
    if (!running) setSeconds(0);
  }, [running]);

  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return (
    <span className="font-mono text-sm text-slate-400">
      {String(m).padStart(2, '0')}:{String(s).padStart(2, '0')}
    </span>
  );
}

export function useSessionTimer(slot: string) {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const secondsRef = useRef(0);

  const start = async () => {
    const res = await api.sessionStart(slot);
    setSessionId(res.session_id);
    setRunning(true);
    secondsRef.current = 0;
  };

  const stop = async () => {
    if (sessionId) {
      await api.sessionEnd(sessionId, secondsRef.current);
    }
    setRunning(false);
    setSessionId(null);
  };

  const onTick = (s: number) => {
    secondsRef.current = s;
  };

  return { running, start, stop, onTick, seconds: secondsRef };
}
