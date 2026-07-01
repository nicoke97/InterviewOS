import { useEffect, useState } from 'react';
import { useI18n } from '../i18n/context';
import {
  interviewStories,
  storyOfDay,
  todayKey,
  type InterviewStory,
} from '../lib/studySession';

function StoryCard({ story, isToday }: { story: InterviewStory; isToday: boolean }) {
  const { t } = useI18n();
  const dayLabel = t(`stories.day_${story.day}`);
  const notesKey = `codenda-story-notes:${story.id}`;
  const fluentKey = `codenda-story-fluent:${story.id}`;
  const [notes, setNotes] = useState('');
  const [fluent, setFluent] = useState(false);

  useEffect(() => {
    setNotes(localStorage.getItem(notesKey) ?? '');
    setFluent(localStorage.getItem(fluentKey) === '1');
  }, [notesKey, fluentKey]);

  const markSaidToday = () => {
    localStorage.setItem(`codenda-story:${todayKey()}:${story.id}`, '1');
  };

  return (
    <div
      className={`card space-y-4 ${isToday ? 'ring-1 ring-brand/40' : ''}`}
      id={story.id}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge-muted text-xs">{dayLabel}</span>
            {isToday && <span className="badge-brand text-xs">{t('stories.today')}</span>}
            <span className="text-xs text-text-dim">{story.role}</span>
          </div>
          <h2 className="mt-1 text-lg font-semibold text-text">{story.title}</h2>
          <p className="mt-1 text-sm text-text-muted">{story.hook}</p>
        </div>
        <label className="flex shrink-0 items-center gap-2 text-xs text-text-muted">
          <input
            type="checkbox"
            checked={fluent}
            onChange={(e) => {
              setFluent(e.target.checked);
              localStorage.setItem(fluentKey, e.target.checked ? '1' : '0');
            }}
          />
          {t('stories.fluent')}
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-dim">
            {t('stories.structure')}
          </p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-text-muted">
            {story.beats.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ol>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-dim">
            {t('stories.anchors')}
          </p>
          <ul className="mt-2 space-y-1 text-sm text-text-muted">
            {story.anchors.map((a) => (
              <li key={a} className="flex gap-2">
                <span className="mt-0.5 text-brand">·</span>
                <span>{a}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface-2 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-dim">
          {t('stories.deliver')}
        </p>
        <ul className="mt-2 space-y-1 text-sm text-text-muted">
          {story.deliver.map((d) => (
            <li key={d} className="flex gap-2">
              <span className="mt-0.5 text-brand">→</span>
              <span>{d}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-sm text-text">{story.closer}</p>
      </div>

      <label className="block text-sm">
        <span className="font-medium text-text">{t('stories.yourVersion')}</span>
        <textarea
          className="mt-1 w-full resize-y rounded border border-border bg-white px-2 py-1.5 text-sm text-text"
          rows={6}
          value={notes}
          placeholder={t('stories.notesPlaceholder')}
          onChange={(e) => {
            setNotes(e.target.value);
            localStorage.setItem(notesKey, e.target.value);
          }}
        />
      </label>

      <button type="button" onClick={markSaidToday} className="btn-secondary text-sm">
        {t('stories.markSaid')}
      </button>
    </div>
  );
}

export function StoriesPage() {
  const { t, locale } = useI18n();
  const today = storyOfDay(new Date(), locale);
  const stories = interviewStories(locale);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">{t('stories.title')}</h1>
        <p className="page-subtitle">{t('stories.subtitle')}</p>
      </div>

      <div className="rounded-lg border border-brand/30 bg-brand/5 px-4 py-3 text-sm text-text-muted">
        {t('stories.intro')}
      </div>

      <div className="space-y-6">
        {stories.map((story) => (
          <StoryCard key={story.id} story={story} isToday={today?.id === story.id} />
        ))}
      </div>
    </div>
  );
}
