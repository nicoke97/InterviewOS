import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type SdeAssignment } from '../lib/api';
import { useI18n } from '../i18n/context';

export function SdeVoicePage() {
  const { locale } = useI18n();
  const [asg, setAsg] = useState<SdeAssignment | null>(null);
  const [text, setText] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [listening, setListening] = useState(false);

  useEffect(() => {
    api.sdeToday().then((d) => {
      const v = d.assignments.find((a) => a.type === 'voice' && !a.completed) || d.assignments.find((a) => a.type === 'voice');
      setAsg(v || null);
    }).catch(() => {});
  }, [locale]);

  const listen = () => {
    const SR = (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognition }).webkitSpeechRecognition
      || (window as unknown as { SpeechRecognition?: new () => SpeechRecognition }).SpeechRecognition;
    if (!SR) {
      setMsg(locale === 'es' ? 'Tu navegador no transcribe. Escribe la respuesta.' : 'No speech API. Type the answer.');
      return;
    }
    const rec = new SR();
    rec.lang = locale === 'es' ? 'es-MX' : 'en-US';
    rec.onresult = (ev: SpeechRecognitionEvent) => {
      setText(ev.results[0][0].transcript);
      setListening(false);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    setListening(true);
    rec.start();
  };

  const submit = async () => {
    if (!asg) return;
    const r = await api.sdeVoice(String(asg.algo_id), String(asg.lang), text);
    setMsg(r.passed
      ? (locale === 'es' ? 'Aprobado. Siguiente idioma / algoritmo.' : 'Passed.')
      : (locale === 'es' ? 'No alcanzó. Habla otra vez; no cambia el idioma.' : 'Not enough. Try again; language stays locked.'));
  };

  if (!asg) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-text-muted">{locale === 'es' ? 'No hay candado de voz ahora.' : 'No voice gate right now.'}</p>
        <Link to="/" className="btn-primary">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
      </div>
    );
  }

  const prompt = locale === 'es' ? String(asg.prompt || '') : String(asg.prompt_en || asg.prompt || '');

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="page-title">{asg.title}</h1>
      <p className="text-sm text-text-muted">{prompt}</p>
      <textarea className="w-full rounded-lg border border-border bg-surface p-3 text-sm" rows={5} value={text} onChange={(e) => setText(e.target.value)} />
      <div className="flex flex-wrap gap-3">
        <button type="button" className="btn-secondary" onClick={listen}>
          {listening ? (locale === 'es' ? 'Escuchando…' : 'Listening…') : (locale === 'es' ? 'Hablar' : 'Speak')}
        </button>
        <button type="button" className="btn-primary" onClick={() => void submit()}>
          {locale === 'es' ? 'Enviar' : 'Submit'}
        </button>
        <Link to="/" className="text-sm text-brand">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
      </div>
      {msg && <p className="text-sm text-text-muted">{msg}</p>}
    </div>
  );
}

interface SpeechRecognition extends EventTarget {
  lang: string;
  start: () => void;
  onresult: ((ev: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
}
interface SpeechRecognitionEvent {
  results: { 0: { 0: { transcript: string } } };
}
