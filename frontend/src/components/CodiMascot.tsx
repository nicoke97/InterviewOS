export type CodiMood = 'idle' | 'happy' | 'celebrate' | 'think' | 'worried' | 'sleep';

interface CodiMascotProps {
  mood?: CodiMood;
  size?: number;
  className?: string;
  animate?: boolean;
}

/**
 * Codi — the tutor mascot. Blue companion whose face tracks learner mood.
 */
export function CodiMascot({ mood = 'idle', size = 72, className = '', animate = true }: CodiMascotProps) {
  const bob = animate && mood !== 'sleep';
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Codi"
      className={`${bob ? 'codi-bob' : ''} ${className}`}
    >
      <ellipse cx="60" cy="109" rx="28" ry="5" fill="#0b1420" opacity="0.14" />

      <line x1="60" y1="20" x2="60" y2="8" stroke="#60a5fa" strokeWidth="3" strokeLinecap="round" />
      <rect
        x="55.5"
        y="2"
        width="9"
        height="9"
        rx="2"
        fill="#2563eb"
        className={animate ? 'codi-antenna' : ''}
      />

      <path
        d="M60 18C33 18 20 38 20 63c0 24 17 41 40 41s40-17 40-41C100 38 87 18 60 18Z"
        fill="#2563eb"
      />
      <ellipse cx="60" cy="70" rx="27" ry="25" fill="#ffffff" opacity="0.16" />

      <path
        d="M22 66c-6 1-10 6-9 12"
        stroke="#1d4ed8"
        strokeWidth="6"
        strokeLinecap="round"
        className={mood === 'celebrate' && animate ? 'codi-wave-l' : ''}
      />
      <path
        d="M98 66c6 1 10 6 9 12"
        stroke="#1d4ed8"
        strokeWidth="6"
        strokeLinecap="round"
        className={mood === 'celebrate' && animate ? 'codi-wave-r' : ''}
      />

      <Face mood={mood} animate={animate} />

      {mood === 'celebrate' && (
        <g className={animate ? 'codi-sparkle' : ''} fill="#ff6b35">
          <path d="M99 30l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" />
          <path d="M18 40l1.5 3.5L23 45l-3.5 1.5L18 50l-1.5-3.5L13 45l3.5-1.5z" />
        </g>
      )}

      {mood === 'sleep' && (
        <g fill="#60a5fa" className={animate ? 'codi-zzz' : ''}>
          <text x="92" y="34" fontFamily="'JetBrains Mono', monospace" fontSize="13" fontWeight="700">z</text>
          <text x="101" y="24" fontFamily="'JetBrains Mono', monospace" fontSize="10" fontWeight="700">z</text>
        </g>
      )}
    </svg>
  );
}

function Face({ mood, animate }: { mood: CodiMood; animate: boolean }) {
  const cheeks = (
    <g fill="#ff8a5c" opacity="0.55">
      <ellipse cx="40" cy="74" rx="5.5" ry="3.5" />
      <ellipse cx="80" cy="74" rx="5.5" ry="3.5" />
    </g>
  );

  if (mood === 'sleep') {
    return (
      <g>
        <path d="M38 62c3-3 9-3 12 0" stroke="#0b1420" strokeWidth="3.5" strokeLinecap="round" fill="none" />
        <path d="M70 62c3-3 9-3 12 0" stroke="#0b1420" strokeWidth="3.5" strokeLinecap="round" fill="none" />
        {cheeks}
        <path d="M54 78c3 3 9 3 12 0" stroke="#0b1420" strokeWidth="3.5" strokeLinecap="round" fill="none" />
      </g>
    );
  }

  if (mood === 'celebrate') {
    return (
      <g>
        <path d="M38 66c2-4 8-4 10 0" stroke="#0b1420" strokeWidth="4" strokeLinecap="round" fill="none" />
        <path d="M72 66c2-4 8-4 10 0" stroke="#0b1420" strokeWidth="4" strokeLinecap="round" fill="none" />
        {cheeks}
        <path d="M50 76c0 8 20 8 20 0 0 0-4 3-10 3s-10-3-10-3Z" fill="#0b1420" />
      </g>
    );
  }

  const eyeOpen = (cx: number) => (
    <g>
      <circle cx={cx} cy="65" r="8.5" fill="#ffffff" />
      <circle cx={cx + 1.5} cy="66" r="4.2" fill="#0b1420" className={animate ? 'codi-blink' : ''} />
      <circle cx={cx + 3} cy="64" r="1.4" fill="#ffffff" />
    </g>
  );

  if (mood === 'worried') {
    return (
      <g>
        <path d="M32 56l14 5" stroke="#0b1420" strokeWidth="3" strokeLinecap="round" />
        <path d="M88 56l-14 5" stroke="#0b1420" strokeWidth="3" strokeLinecap="round" />
        {eyeOpen(42)}
        {eyeOpen(78)}
        <path d="M50 82c3-4 17-4 20 0" stroke="#0b1420" strokeWidth="3.5" strokeLinecap="round" fill="none" />
      </g>
    );
  }

  if (mood === 'think') {
    return (
      <g>
        <path d="M33 57l13 3" stroke="#0b1420" strokeWidth="3" strokeLinecap="round" />
        {eyeOpen(42)}
        {eyeOpen(78)}
        {cheeks}
        <path d="M52 80h14" stroke="#0b1420" strokeWidth="3.5" strokeLinecap="round" />
      </g>
    );
  }

  const smile =
    mood === 'happy'
      ? 'M48 76c4 6 20 6 24 0'
      : 'M50 77c3 4 17 4 20 0';
  return (
    <g>
      {eyeOpen(42)}
      {eyeOpen(78)}
      {cheeks}
      <path d={smile} stroke="#0b1420" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    </g>
  );
}
