/** Accept Python that matches the expected solution except for insignificant syntax. */

const WORD = /[A-Za-z0-9_]/;
const SPACE = /[ \t]/;
const STRING_PREFIX = /[rRuUfFbB]/;
const MULTI_OP = new Set([
  '==',
  '!=',
  '<=',
  '>=',
  '+=',
  '-=',
  '*=',
  '/=',
  '%=',
  '&=',
  '|=',
  '^=',
  '//',
  '**',
  '<<',
  '>>',
  '->',
  ':=',
  '<>',
  '//=',
  '**=',
  '<<=',
  '>>=',
]);

type StringFrame = {
  quote: "'" | '"';
  triple: boolean;
  fString: boolean;
  exprDepth: number;
  escaped: boolean;
};

function isWord(ch: string): boolean {
  return WORD.test(ch);
}

function gluesToOperator(a: string, b: string): boolean {
  return MULTI_OP.has(a + b);
}

function gluesFloat(a: string, b: string): boolean {
  return (a === '.' && /\d/.test(b)) || (b === '.' && /\d/.test(a));
}

function hasFPrefix(code: string, quoteIndex: number): boolean {
  let j = quoteIndex - 1;
  while (j >= 0 && STRING_PREFIX.test(code[j])) j -= 1;
  const prefix = code.slice(j + 1, quoteIndex).toLowerCase();
  if (!prefix) return false;
  if (j >= 0 && isWord(code[j])) return false;
  return prefix.includes('f');
}

function scanTo(code: string, end: number): StringFrame[] {
  const frames: StringFrame[] = [];
  let i = 0;

  while (i < end) {
    const top = frames[frames.length - 1];
    const inExpr = !top || top.exprDepth > 0;

    if (inExpr) {
      if (top && code[i] === '{') {
        top.exprDepth += 1;
        i += 1;
        continue;
      }
      if (top && code[i] === '}') {
        top.exprDepth = Math.max(0, top.exprDepth - 1);
        i += 1;
        continue;
      }
      if (code[i] === "'" || code[i] === '"') {
        const quote = code[i] as "'" | '"';
        const triple = code.startsWith(quote.repeat(3), i);
        frames.push({
          quote,
          triple,
          fString: hasFPrefix(code, i),
          exprDepth: 0,
          escaped: false,
        });
        i += triple ? 3 : 1;
        continue;
      }
      i += 1;
      continue;
    }

    if (top.escaped) {
      top.escaped = false;
      i += 1;
      continue;
    }
    if (code[i] === '\\' && !top.triple) {
      top.escaped = true;
      i += 1;
      continue;
    }
    if (top.fString && code[i] === '{') {
      if (code[i + 1] === '{') {
        i += 2;
        continue;
      }
      top.exprDepth = 1;
      i += 1;
      continue;
    }
    if (top.triple) {
      if (code.startsWith(top.quote.repeat(3), i)) {
        frames.pop();
        i += 3;
        continue;
      }
    } else if (code[i] === top.quote) {
      frames.pop();
      i += 1;
      continue;
    }
    i += 1;
  }

  return frames;
}

function inStringContent(code: string, index: number): boolean {
  const top = scanTo(code, index).at(-1);
  return Boolean(top && top.exprDepth === 0);
}

function isStringDelimiter(code: string, index: number): boolean {
  const ch = code[index];
  if (ch !== "'" && ch !== '"') return false;
  const top = scanTo(code, index).at(-1);
  if (!top || top.exprDepth > 0) return true;
  if (top.escaped) return false;
  if (top.triple) return code.startsWith(top.quote.repeat(3), index);
  return ch === top.quote;
}

function lineStart(code: string, index: number): number {
  let i = index;
  while (i > 0 && code[i - 1] !== '\n') i -= 1;
  return i;
}

function firstNonWsOnLine(code: string, start: number): number {
  let i = start;
  while (i < code.length && SPACE.test(code[i])) i += 1;
  return i;
}

/** Spaces/tabs from the start of the line, including just before the first code character. */
function inIndentZone(code: string, index: number): boolean {
  const start = lineStart(code, index);
  return index <= firstNonWsOnLine(code, start);
}

function isIndentSpace(code: string, index: number): boolean {
  if (!SPACE.test(code[index] ?? '')) return false;
  const start = lineStart(code, index);
  for (let i = start; i <= index; i += 1) {
    if (!SPACE.test(code[i])) return false;
  }
  return true;
}

function lastSignificant(code: string, end: number): string {
  for (let i = end - 1; i >= 0; i -= 1) {
    if (code[i] === '\n') return '\n';
    if (!SPACE.test(code[i])) return code[i];
  }
  return '';
}

function nextSignificantIndex(code: string, start: number): number {
  for (let i = start; i < code.length; i += 1) {
    if (code[i] === '\n' || !SPACE.test(code[i])) return i;
  }
  return code.length;
}

function needsSeparator(prev: string, next: string): boolean {
  if (!prev || !next || prev === '\n' || next === '\n') return false;
  if (isWord(prev) && isWord(next)) return true;
  if (gluesToOperator(prev, next)) return true;
  if (gluesFloat(prev, next)) return true;
  return false;
}

function isOptionalSpace(expected: string, index: number): boolean {
  if (!SPACE.test(expected[index] ?? '')) return false;
  if (inStringContent(expected, index)) return false;
  if (isIndentSpace(expected, index)) return false;

  const prev = lastSignificant(expected, index);
  const nextIdx = nextSignificantIndex(expected, index + 1);
  const next = expected[nextIdx] ?? '';
  if (!needsSeparator(prev, next)) return true;
  return nextIdx > index + 1;
}

function isOptionalInsertion(expected: string, index: number): boolean {
  if (inStringContent(expected, index)) return false;
  if (inIndentZone(expected, index)) return false;
  const prev = expected[index - 1] ?? '';
  const next = expected[index] ?? '';
  if (!prev || SPACE.test(prev) || SPACE.test(next) || next === '\n') return true;
  return !needsSeparator(prev, next);
}

function charsMatch(expectedCh: string, typedCh: string, expected: string, index: number): boolean {
  if (expectedCh === typedCh) return true;
  if ((expectedCh === "'" || expectedCh === '"') && (typedCh === "'" || typedCh === '"')) {
    return isStringDelimiter(expected, index);
  }
  return false;
}

function skipOptionalSpaces(expected: string, typed: string): string {
  let built = typed;
  while (built.length < expected.length && isOptionalSpace(expected, built.length)) {
    built += expected[built.length];
  }
  return built;
}

/** Try to consume `ch` against `expected`. Returns the new typed prefix, or null. */
export function acceptChar(expected: string, typed: string, ch: string): string | null {
  if (ch === '\r') return typed;
  if (typed.length > expected.length) return null;

  if (SPACE.test(ch)) {
    if (typed.length < expected.length && SPACE.test(expected[typed.length])) {
      if (!isOptionalSpace(expected, typed.length) && expected[typed.length] !== ch) return null;
      return typed + expected[typed.length];
    }
    if (isOptionalInsertion(expected, typed.length)) return typed;
    return null;
  }

  const built = skipOptionalSpaces(expected, typed);
  if (built.length >= expected.length) return null;
  if (!charsMatch(expected[built.length], ch, expected, built.length)) return null;
  return built + expected[built.length];
}

export function acceptText(expected: string, typed: string, text: string): string {
  let updated = typed;
  for (const ch of text) {
    const next = acceptChar(expected, updated, ch);
    if (next === null) break;
    updated = next;
  }
  return updated;
}

export function backspaceTyped(expected: string, typed: string): string {
  if (!typed) return '';
  let next = typed.slice(0, -1);
  while (next.length > 0 && isOptionalSpace(expected, next.length - 1)) {
    next = next.slice(0, -1);
  }
  return next;
}
