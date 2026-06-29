import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '../i18n/context';
import {
  STUDY_LANG_LABEL,
  languageOfDay,
  storyOfDay,
  todayKey,
  type StudyLang,
} from '../lib/studySession';

export function SessionRitual({ lockMinutes }: { lockMinutes: number }) {
  const { t } = useI18n();
  const lang = languageOfDay();

  return (
    <div className="rounded-lg border border-brand/30 bg-brand/5 px-4 py-3 text-sm">
      <p className="font-medium text-text">{t('studySession.ritualTitle')}</p>
      <ol className="mt-2 list-decimal space-y-1 pl-5 text-text-muted">
        <li>{t('studySession.ritual1')}</li>
        <li>{t('studySession.ritual2', { min: lockMinutes })}</li>
        <li>{t('studySession.ritual3')}</li>
        <li>{t('studySession.ritual4', { lang: STUDY_LANG_LABEL[lang] })}</li>
      </ol>
      <p className="mt-2 text-xs text-text-dim">{t('studySession.judgeNote')}</p>
    </div>
  );
}

export function InterviewStoryCard() {
  const { t, locale } = useI18n();
  const story = storyOfDay(new Date(), locale);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!story) return;
    const key = `codenda-story:${todayKey()}:${story.id}`;
    setDone(localStorage.getItem(key) === '1');
  }, [story]);

  if (!story) {
    return (
      <p className="text-sm text-text-dim">{t('studySession.storyOffDay')}</p>
    );
  }

  const toggle = () => {
    const key = `codenda-story:${todayKey()}:${story.id}`;
    const next = !done;
    setDone(next);
    localStorage.setItem(key, next ? '1' : '0');
  };

  return (
    <div className="rounded-lg border border-border px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-text-dim">
            {t('studySession.storyToday')}
          </p>
          <p className="mt-1 text-sm font-medium text-text">{story.title}</p>
        </div>
        <button type="button" onClick={toggle} className="btn-secondary text-xs">
          {done ? t('studySession.storyDone') : t('studySession.storyMark')}
        </button>
      </div>
      <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-text-muted">
        {story.beats.map((beat) => (
          <li key={beat}>{beat}</li>
        ))}
      </ol>
      <p className="mt-2 text-xs text-text-dim">{t('studySession.storyHint')}</p>
      <Link to={`/stories#${story.id}`} className="mt-2 inline-block text-xs text-brand hover:underline">
        {t('studySession.storyOpen')}
      </Link>
    </div>
  );
}

export function SecondLanguagePad({ problemId }: { problemId: string }) {
  const { t } = useI18n();
  const lang: StudyLang = languageOfDay();
  const key = `codenda-second-pass:${todayKey()}:${problemId}`;
  const [text, setText] = useState('');

  useEffect(() => {
    setText(localStorage.getItem(key) ?? '');
  }, [key]);

  return (
    <div className="rounded-lg border border-dashed border-border px-4 py-3">
      <p className="text-sm font-medium text-text">
        {t('studySession.secondLangTitle', { lang: STUDY_LANG_LABEL[lang] })}
      </p>
      <p className="mt-1 text-xs text-text-dim">{t('studySession.secondLangHint')}</p>
      <textarea
        className="mt-3 w-full resize-y rounded border border-border bg-stone-50 px-2 py-1.5 font-mono text-xs text-text"
        rows={8}
        value={text}
        spellCheck={false}
        placeholder={t('studySession.secondLangPlaceholder', { lang: STUDY_LANG_LABEL[lang] })}
        onChange={(e) => {
          setText(e.target.value);
          localStorage.setItem(key, e.target.value);
        }}
      />
    </div>
  );
}

export function ComplexityLog({ problemId }: { problemId: string }) {
  const { t } = useI18n();
  const key = `codenda-complexity:${todayKey()}:${problemId}`;
  const [text, setText] = useState('');

  useEffect(() => {
    setText(localStorage.getItem(key) ?? '');
  }, [key]);

  return (
    <label className="block text-sm">
      <span className="font-medium text-text">{t('studySession.complexity')}</span>
      <input
        className="mt-1 w-full rounded border border-border bg-white px-2 py-1.5 font-mono text-xs text-text"
        value={text}
        placeholder="O(n) time, O(n) space"
        onChange={(e) => {
          setText(e.target.value);
          localStorage.setItem(key, e.target.value);
        }}
      />
    </label>
  );
}

const OUTCOMES = ['solo', 'hint', 'fail'] as const;

export function StudyOutcome({ problemId }: { problemId: string }) {
  const { t } = useI18n();
  const key = `codenda-outcome:${todayKey()}:${problemId}`;
  const [value, setValue] = useState('');

  useEffect(() => {
    setValue(localStorage.getItem(key) ?? '');
  }, [key]);

  return (
    <label className="block text-sm">
      <span className="font-medium text-text">{t('studySession.outcome')}</span>
      <select
        className="mt-1 w-full rounded border border-border bg-white px-2 py-1.5 text-sm text-text"
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          localStorage.setItem(key, e.target.value);
        }}
      >
        <option value="">{t('studySession.outcomePick')}</option>
        {OUTCOMES.map((id) => (
          <option key={id} value={id}>{t(`studySession.outcome_${id}`)}</option>
        ))}
      </select>
    </label>
  );
}

