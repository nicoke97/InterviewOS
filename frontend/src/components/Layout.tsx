import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { api } from '../lib/api';
import { FALLBACK_LEVELS, type CurriculumLevel } from '../lib/levels';

export function Layout({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [levelsOpen, setLevelsOpen] = useState(false);
  const levelsRef = useRef<HTMLDivElement>(null);
  const [levels, setLevels] = useState<CurriculumLevel[]>(FALLBACK_LEVELS);
  const [odooLevels, setOdooLevels] = useState<CurriculumLevel[]>([]);

  const isActive = (to: string) =>
    to === '/' ? loc.pathname === '/' : loc.pathname.startsWith(to);
  const isLevelActive = (id: string) => loc.pathname.startsWith(`/${id}/`) || loc.pathname === `/${id}`;
  const isOrientadorInsight = loc.pathname === '/orientador';

  useEffect(() => {
    setMenuOpen(false);
    setLevelsOpen(false);
  }, [loc.pathname]);

  useEffect(() => {
    api.curriculum()
      .then((c) => {
        const py = c.levels as CurriculumLevel[] | undefined;
        const od = c.odoo_levels as CurriculumLevel[] | undefined;
        if (py?.length) setLevels(py);
        if (od?.length) setOdooLevels(od);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!levelsOpen) return;
    const handler = (e: MouseEvent) => {
      if (levelsRef.current && !levelsRef.current.contains(e.target as Node)) setLevelsOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [levelsOpen]);

  return (
    <div className="app-shell">
      <header className="sticky top-0 z-50 border-b border-border bg-bg">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4">
          <Link to="/" className="flex shrink-0 items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-bg">I</div>
            <span className="text-base font-semibold text-text">InterviewOS</span>
          </Link>

          <nav className="hidden items-center justify-end gap-0.5 md:flex">
            <NavLink to="/" label="Dashboard" active={loc.pathname === '/'} />

            <div ref={levelsRef} className="relative">
              <button
                type="button"
                onClick={() => setLevelsOpen((o) => !o)}
                className={`inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  levels.some((l) => isLevelActive(l.id)) || odooLevels.some((l) => isLevelActive(l.id))
                    ? 'bg-surface-2 text-text'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                Niveles
                <svg className={`h-3.5 w-3.5 transition-transform ${levelsOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {levelsOpen && (
                <div className="nav-dropdown max-h-[70vh] overflow-y-auto">
                  <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-text-dim">Python</p>
                  {levels.map((lvl) => (
                    <Link
                      key={lvl.id}
                      to={`/${lvl.id}/roadmap`}
                      onClick={() => setLevelsOpen(false)}
                      className="nav-dropdown-item"
                    >
                      <span>Nivel {lvl.letter}</span>
                      <span className="text-xs text-text-dim">{lvl.title.replace(/^Level \w+ — /, '')}</span>
                    </Link>
                  ))}
                  {odooLevels.length > 0 && (
                    <>
                      <p className="mt-2 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-text-dim">Odoo</p>
                      {odooLevels.map((lvl) => (
                        <Link
                          key={lvl.id}
                          to={`/${lvl.id}/roadmap`}
                          onClick={() => setLevelsOpen(false)}
                          className="nav-dropdown-item"
                        >
                          <span>{lvl.title}</span>
                        </Link>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>

            <NavLink to="/orientador" label="Orientador" active={isOrientadorInsight} />
            <NavLink to="/settings" label="Settings" active={isActive('/settings')} />
          </nav>

          <button
            type="button"
            className="rounded-lg p-2 text-text-muted hover:bg-surface hover:text-text md:hidden"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Toggle menu"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {menuOpen && (
          <nav className="border-t border-border px-5 py-3 md:hidden">
            <div className="flex flex-col gap-0.5">
              <MobileLink to="/" label="Dashboard" active={loc.pathname === '/'} />
              <p className="px-3 pt-2 text-xs font-medium uppercase tracking-wide text-text-dim">Niveles Python</p>
              {levels.map((lvl) => (
                <MobileLink key={lvl.id} to={`/${lvl.id}/roadmap`} label={`Nivel ${lvl.letter}`} active={isLevelActive(lvl.id)} />
              ))}
              {odooLevels.length > 0 && (
                <>
                  <p className="px-3 pt-2 text-xs font-medium uppercase tracking-wide text-text-dim">Odoo</p>
                  {odooLevels.map((lvl) => (
                    <MobileLink key={lvl.id} to={`/${lvl.id}/roadmap`} label={lvl.title} active={isLevelActive(lvl.id)} />
                  ))}
                </>
              )}
              <MobileLink to="/orientador" label="Orientador" active={isOrientadorInsight} />
              <MobileLink to="/settings" label="Settings" active={isActive('/settings')} />
            </div>
          </nav>
        )}
      </header>

      <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>
    </div>
  );
}

function NavLink({ to, label, active }: { to: string; label: string; active: boolean }) {
  return (
    <Link
      to={to}
      className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
        active ? 'bg-surface-2 text-text' : 'text-text-muted hover:text-text'
      }`}
    >
      {label}
    </Link>
  );
}

function MobileLink({ to, label, active }: { to: string; label: string; active: boolean }) {
  return (
    <Link
      to={to}
      className={`rounded-lg px-3 py-2.5 text-sm font-medium ${active ? 'bg-surface-2 text-text' : 'text-text-muted'}`}
    >
      {label}
    </Link>
  );
}
