import { useEffect, useMemo, useRef, useState } from 'react';
import { assembleTemplate, inferSlotAnswers } from '../lib/slotAnswers';

type CharCell = { ch: string; inSlot: boolean };

const COLOR_TYPED = '#1c1917';
const COLOR_GHOST = '#78716c';
const COLOR_GHOST_SLOT = '#57534e';
const COLOR_SLOT_BG = '#e7e5e4';

/** Flatten template + slot fills into the exact character stream the user types. */
function buildCharMap(template: string, slotAnswers: string[], expected: string): CharCell[] {
  const t = template.replace(/\r\n/g, '\n');
  const exp = expected.replace(/\r\n/g, '\n').trimEnd();
  const cells: CharCell[] = [];
  let slotIdx = 0;
  let i = 0;

  while (i < t.length) {
    if (t.startsWith('___', i)) {
      const fill = slotAnswers[slotIdx++] ?? '___';
      for (const ch of fill) cells.push({ ch, inSlot: true });
      i += 3;
    } else {
      cells.push({ ch: t[i], inSlot: false });
      i += 1;
    }
  }

  const built = cells.map((c) => c.ch).join('');
  if (built.trimEnd() !== exp) {
    return exp.split('').map((ch) => ({ ch, inSlot: false }));
  }
  return cells;
}

function groupLineCells(cells: CharCell[]): CharCell[][] {
  if (!cells.length) return [];
  const groups: CharCell[][] = [[cells[0]]];
  for (let i = 1; i < cells.length; i++) {
    const prev = groups[groups.length - 1][0].inSlot;
    if (cells[i].inSlot === prev) {
      groups[groups.length - 1].push(cells[i]);
    } else {
      groups.push([cells[i]]);
    }
  }
  return groups;
}

function acceptChar(expected: string, typed: string, ch: string): string | null {
  const next = typed.length;
  if (next >= expected.length || ch !== expected[next]) return null;
  return typed + ch;
}

function acceptText(expected: string, typed: string, text: string): string {
  let updated = typed;
  for (const ch of text) {
    const next = acceptChar(expected, updated, ch);
    if (next === null) break;
    updated = next;
  }
  return updated;
}

interface KumonCodeInputProps {
  template: string;
  prompt: string;
  slotAnswers?: string[];
  referenceCode?: string;
  onChange: (code: string) => void;
}

export function KumonCodeInput({
  template,
  prompt,
  slotAnswers: slotAnswersProp = [],
  referenceCode = '',
  onChange,
}: KumonCodeInputProps) {
  const normalizedTemplate = template.replace(/\r\n/g, '\n');

  const slotAnswers = useMemo(() => {
    if (slotAnswersProp.length > 0) return slotAnswersProp;
    return inferSlotAnswers(normalizedTemplate, prompt);
  }, [slotAnswersProp, normalizedTemplate, prompt]);

  const expected = useMemo(() => {
    const fromRef = referenceCode.replace(/\r\n/g, '\n').trimEnd();
    if (fromRef) return fromRef;
    return assembleTemplate(normalizedTemplate, slotAnswers).trimEnd();
  }, [referenceCode, normalizedTemplate, slotAnswers]);

  const charMap = useMemo(
    () => buildCharMap(normalizedTemplate, slotAnswers, expected),
    [normalizedTemplate, slotAnswers, expected],
  );

  const [typed, setTyped] = useState('');
  const surfaceRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTyped('');
    onChange('');
  }, [expected]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Backspace') {
      e.preventDefault();
      if (typed.length > 0) {
        const next = typed.slice(0, -1);
        setTyped(next);
        onChange(next);
      }
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const next = acceptChar(expected, typed, '\n');
      if (next !== null) {
        setTyped(next);
        onChange(next);
      }
      return;
    }
    if (e.key === 'Tab' || e.key.startsWith('Arrow')) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key.length !== 1) {
      e.preventDefault();
      return;
    }
    e.preventDefault();
    const next = acceptChar(expected, typed, e.key);
    if (next !== null) {
      setTyped(next);
      onChange(next);
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const updated = acceptText(expected, typed, e.clipboardData.getData('text'));
    if (updated !== typed) {
      setTyped(updated);
      onChange(updated);
    }
  };

  if (!expected) {
    return (
      <div
        className="min-h-[4.5rem] rounded border border-dashed px-2 py-2 text-xs"
        style={{ borderColor: '#a8a29e', background: '#f5f5f4', color: '#78716c' }}
      >
        Click and type your answer here.
      </div>
    );
  }

  let charIndex = 0;

  const charStyle = { fontFamily: 'ui-monospace, monospace', fontSize: '0.75rem', lineHeight: '1.625rem' };

  const cursor = (
    <span
      className="mr-px inline-block animate-pulse align-middle"
      style={{ width: 2, height: '1em', background: COLOR_TYPED }}
    />
  );

  const renderChar = (ch: string, key: string, inSlot: boolean) => {
    const idx = charIndex++;
    const done = idx < typed.length;
    return (
      <span key={key}>
        {idx === typed.length && cursor}
        <span style={{ color: done ? COLOR_TYPED : inSlot ? COLOR_GHOST_SLOT : COLOR_GHOST }}>
          {ch}
        </span>
      </span>
    );
  };

  const lineRows: CharCell[][] = [];
  let currentLine: CharCell[] = [];
  for (const cell of charMap) {
    if (cell.ch === '\n') {
      lineRows.push(currentLine);
      currentLine = [];
    } else {
      currentLine.push(cell);
    }
  }
  lineRows.push(currentLine);

  return (
    <div
      ref={surfaceRef}
      tabIndex={0}
      role="textbox"
      aria-label="Type the code"
      aria-multiline
      onKeyDown={handleKeyDown}
      onPaste={handlePaste}
      onClick={() => surfaceRef.current?.focus()}
      className="min-h-[4.5rem] cursor-text rounded border border-dashed px-2 py-2 outline-none"
      style={{ borderColor: '#a8a29e', background: '#fafaf9' }}
    >
      <div style={charStyle}>
        {lineRows.map((lineCells, li) => {
          const groups = groupLineCells(lineCells);
          const lineStartIndex = charIndex;

          const lineContent = groups.length === 0 ? (
            lineStartIndex === typed.length ? cursor : null
          ) : (
            groups.map((group, gi) => {
              const inner = group.map((cell, ci) =>
                renderChar(cell.ch, `${li}-${gi}-${ci}`, cell.inSlot),
              );
              if (group[0].inSlot) {
                return (
                  <span
                    key={gi}
                    className="whitespace-pre rounded-sm"
                    style={{ background: COLOR_SLOT_BG, boxShadow: 'inset 0 -2px 0 0 #d6d3d1' }}
                  >
                    {inner}
                  </span>
                );
              }
              return (
                <span key={gi} className="whitespace-pre">
                  {inner}
                </span>
              );
            })
          );

          // Count the newline character in charIndex (except after the last line).
          const atLineBreak = li < lineRows.length - 1;
          if (atLineBreak) {
            const nlIdx = charIndex++;
            if (nlIdx === typed.length) {
              return (
                <div key={li} className="min-h-[1.625rem]">
                  {lineContent}
                  {cursor}
                </div>
              );
            }
          }

          return (
            <div key={li} className="min-h-[1.625rem]">
              {lineContent}
            </div>
          );
        })}
        {charIndex === typed.length && cursor}
      </div>
    </div>
  );
}

export function hasPlaceholders(template: string): boolean {
  return template.includes('___');
}
