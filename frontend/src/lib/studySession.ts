const LANGS = ['csharp', 'python', 'typescript'] as const;
export type StudyLang = (typeof LANGS)[number];
export type OrientadorTrack = 'python' | 'leetcodes';

export const ORIENTADOR_TRACK_KEY = 'codenda-orientador-track';

export function readOrientadorTrack(): OrientadorTrack {
  try {
    const stored = localStorage.getItem(ORIENTADOR_TRACK_KEY);
    if (stored === 'python' || stored === 'leetcodes') return stored;
  } catch {
    /* ignore */
  }
  return 'leetcodes';
}

export function writeOrientadorTrack(track: OrientadorTrack) {
  try {
    localStorage.setItem(ORIENTADOR_TRACK_KEY, track);
  } catch {
    /* ignore */
  }
}

export function defaultMinutesForTrack(track: OrientadorTrack): number {
  return track === 'leetcodes' ? 60 : 15;
}

export const STUDY_LANG_LABEL: Record<StudyLang, string> = {
  csharp: 'C#',
  python: 'Python',
  typescript: 'TypeScript',
};

export function languageOfDay(d = new Date()): StudyLang {
  const utc = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
  return LANGS[Math.floor(utc / 86_400_000) % LANGS.length];
}

export function isInterviewStoryDay(d = new Date()): boolean {
  const day = d.getDay();
  return day === 1 || day === 3 || day === 5;
}

export type StoryKind = 'work' | 'product';

export interface InterviewStory {
  id: string;
  day: 'mon' | 'wed' | 'fri';
  kind: StoryKind;
  title: string;
  role: string;
  hook: string;
  beats: string[];
  anchors: string[];
  deliver: string[];
  closer: string;
}

type StoryLocale = 'en' | 'es';

const WORK_BEATS: Record<StoryLocale, string[]> = {
  es: [
    'Qué estaba roto / qué pedían',
    'Cómo lo diseñaste (el corte, no el tutorial)',
    'Qué se rompía por el camino',
    'Qué cortaste y cómo supiste que estaba bien',
    'Qué harías distinto',
  ],
  en: [
    'What was broken / what they asked for',
    'How you designed it (the cut, not the tutorial)',
    'What broke along the way',
    'What you cut and how you knew it was right',
    'What you would do differently',
  ],
};

const STORIES: Record<StoryLocale, InterviewStory[]> = {
  es: [
    {
      id: 'ebay',
      day: 'mon',
      kind: 'work',
      title: 'eBay SOAP → REST',
      role: 'eLink · Solera (SDE I)',
      hook: 'eBay deprecó llamadas del Trading API sin anunciarlo y rompió el sync de sellers.',
      beats: WORK_BEATS.es,
      anchors: [
        'eLink sincroniza listings, orders e inventario con eBay.',
        'Cliente C# generado del WSDL; XML; Faults metidos dentro de un 200 OK.',
        'Una sola interfaz para listings/orders/inventory (no tres caminos).',
        'Dual-run: correr SOAP y REST en paralelo y comparar payloads.',
        'REST como único writer solo cuando los diffs quedaron en cero.',
      ],
      deliver: [
        '~3 min. Arranca por el corte (una interfaz, dual-run), no por el WSDL.',
        'Enseña que sabías cuándo era seguro cortar: el diff de payloads en cero.',
      ],
      closer: 'Distinto: contract tests y flag por operación desde el día 1, no al final.',
    },
    {
      id: 'dotnet',
      day: 'wed',
      kind: 'work',
      title: '.NET Framework 4.8 → Core 8',
      role: 'Solera (SDE II)',
      hook: '15 servicios interconectados que había que migrar sin tumbar producción.',
      beats: WORK_BEATS.es,
      anchors: [
        'El proyecto real era el grafo de dependencias, no el compilador.',
        '15 servicios: mapear quién le escribe a quién antes de tocar nada.',
        'Dual-run y compatibilidad primero; cutover cuando Core era el único writer.',
        'Además: TFS/TFVC → GitHub + pipelines YAML para esos servicios.',
        'Comparar artefactos de build antes de cortar TFS.',
      ],
      deliver: [
        '~3 min. El héroe es el grafo y el cutover, no “lo hizo Copilot”.',
        'Cuenta cómo cortaste por hojas del grafo, no big-bang.',
      ],
      closer: 'Distinto: automatizar el diff de artefactos antes, no revisar a mano.',
    },
    {
      id: 'slabhq',
      day: 'fri',
      kind: 'product',
      title: 'SlabHQ',
      role: 'Founder',
      hook: 'Infra para sellers de TCG en México: Mercado Libre, no eBay US.',
      beats: [
        'Por qué existe (el problema real)',
        'Qué es el producto (el corte, no la lista de features)',
        'Qué está live y qué está a medias',
        'Una decisión de founder y su tradeoff',
        'El siguiente hito',
      ],
      anchors: [
        'Por qué: el mercado mexicano vive en Mercado Libre, no en eBay US.',
        'De binder físico a listing desk: escanear, inventariar, publicar a canales.',
        'Live: inventario + binder público + listings a Mercado Libre; scan/list con IA.',
        'A medias: pagos, eBay US, sync entre canales.',
        'Eres founder: hablas de decisiones y tradeoffs, no de tickets.',
      ],
      deliver: [
        '~3 min como pitch, no como demo. Problema → producto → qué está live.',
        'Una decisión con tradeoff (p. ej. ML primero en vez de eBay US) y por qué.',
      ],
      closer: 'Cierra con el siguiente hito y qué desbloquea para el seller.',
    },
  ],
  en: [
    {
      id: 'ebay',
      day: 'mon',
      kind: 'work',
      title: 'eBay SOAP → REST',
      role: 'eLink · Solera (SDE I)',
      hook: 'eBay deprecated Trading API calls without announcing it and broke seller sync.',
      beats: WORK_BEATS.en,
      anchors: [
        'eLink syncs listings, orders, and inventory with eBay.',
        'C# client generated from the WSDL; XML; Faults stuffed inside a 200 OK.',
        'One interface for listings/orders/inventory (not three paths).',
        'Dual-run: run SOAP and REST in parallel and compare payloads.',
        'REST as the only writer only when diffs hit zero.',
      ],
      deliver: [
        '~3 min. Start with the cut (one interface, dual-run), not the WSDL.',
        'Show you knew when it was safe to cut: payload diffs at zero.',
      ],
      closer: 'Differently: contract tests and a per-operation flag from day 1, not at the end.',
    },
    {
      id: 'dotnet',
      day: 'wed',
      kind: 'work',
      title: '.NET Framework 4.8 → Core 8',
      role: 'Solera (SDE II)',
      hook: '15 interconnected services that had to migrate without taking production down.',
      beats: WORK_BEATS.en,
      anchors: [
        'The real project was the dependency graph, not the compiler.',
        '15 services: map who writes to whom before touching anything.',
        'Dual-run and compatibility first; cutover when Core was the only writer.',
        'Also: TFS/TFVC → GitHub + YAML pipelines for those services.',
        'Compare build artifacts before cutting TFS.',
      ],
      deliver: [
        '~3 min. The hero is the graph and the cutover, not “Copilot did it”.',
        'Tell how you cut by graph leaves, not a big-bang.',
      ],
      closer: 'Differently: automate the artifact diff earlier, not review by hand.',
    },
    {
      id: 'slabhq',
      day: 'fri',
      kind: 'product',
      title: 'SlabHQ',
      role: 'Founder',
      hook: 'Infra for TCG sellers in Mexico: Mercado Libre, not eBay US.',
      beats: [
        'Why it exists (the real problem)',
        'What the product is (the cut, not the feature list)',
        "What's live and what's half-done",
        'One founder decision and its tradeoff',
        'The next milestone',
      ],
      anchors: [
        'Why: the Mexican market lives on Mercado Libre, not eBay US.',
        'From physical binder to listing desk: scan, inventory, publish to channels.',
        'Live: inventory + public binder + Mercado Libre listings; AI scan/list.',
        'Half-done: payments, eBay US, cross-channel sync.',
        "You're a founder: talk decisions and tradeoffs, not tickets.",
      ],
      deliver: [
        '~3 min as a pitch, not a demo. Problem → product → what’s live.',
        'One decision with a tradeoff (e.g. Mercado Libre first instead of eBay US) and why.',
      ],
      closer: 'Close with the next milestone and what it unlocks for the seller.',
    },
  ],
};

const DAY_TO_STORY: Record<number, number> = { 1: 0, 3: 1, 5: 2 };

export function interviewStories(locale: StoryLocale = 'en'): InterviewStory[] {
  return STORIES[locale] ?? STORIES.en;
}

export function storyOfDay(d = new Date(), locale: StoryLocale = 'en'): InterviewStory | null {
  if (!isInterviewStoryDay(d)) return null;
  return interviewStories(locale)[DAY_TO_STORY[d.getDay()]];
}

export function todayKey(d = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function hintLockKey(problemId: string, day = new Date()): string {
  return `codenda-hint-lock:${todayKey(day)}:${problemId}`;
}

export function ensureHintLockStart(problemId: string, now = Date.now()): number {
  const key = hintLockKey(problemId);
  try {
    const existing = localStorage.getItem(key);
    if (existing) return Number(existing);
    localStorage.setItem(key, String(now));
    return now;
  } catch {
    return now;
  }
}

export function hintUnlockAt(startedAt: number, lockMinutes: number): number {
  return startedAt + lockMinutes * 60_000;
}

export function formatCountdown(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}
