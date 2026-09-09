import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { api, type ReturnExamStatus } from '../lib/api';
import { useCurriculumLevels, type CurriculumLevel } from '../lib/levels';
import { LanguageToggle } from '../i18n/LanguageToggle';
import { CodiCompanion } from './CodiCompanion';
import { useI18n } from '../i18n/context';

function trackLevelTitle(
  lvl: CurriculumLevel,
  track: 'csharp' | 'odoo',
  t: (key: string, vars?: Record<string, string | number>) => string,
): string {
  const key = `levels.${track}.${lvl.id}`;
  const translated = t(key);
  return translated === key ? lvl.title : translated;
}

function pathLevelId(pathname: string): string | null {
  const match = pathname.match(/^\/([a-z][a-z0-9-]*)\b/i);
  if (!match) return null;
  const id = match[1].toLowerCase();
  if (
    ['stories', 'projects', 'leetcodes', 'orientador', 'settings', 'return-exam', 'kumon', 'sde'].includes(id)
  ) {
    return null;
  }
  return id;
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { t, locale } = useI18n();
  const loc = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [languagesOpen, setLanguagesOpen] = useState(true);
  const [csharpOpen, setCsharpOpen] = useState(false);
  const [pythonOpen, setPythonOpen] = useState(false);
  const [companiesOpen, setCompaniesOpen] = useState(false);
  const levels = useCurriculumLevels();
  const [odooLevels, setOdooLevels] = useState<CurriculumLevel[]>([]);
  const [csharpLevels, setCsharpLevels] = useState<CurriculumLevel[]>([]);
  const [returnExam, setReturnExam] = useState<ReturnExamStatus | null>(null);

  const isActive = (to: string) =>
    to === '/' ? loc.pathname === '/' : loc.pathname.startsWith(to);
  const isLevelActive = (id: string) => loc.pathname.startsWith(`/${id}/`) || loc.pathname === `/${id}`;
  const isOrientadorInsight = loc.pathname === '/orientador';
  const isLeetcodesActive = loc.pathname.startsWith('/leetcodes');
  const isProjectsActive = loc.pathname.startsWith('/stories') || loc.pathname.startsWith('/projects');
  const isLeetcodeWorkspace = (
    (/^\/leetcodes\/(orientador\/[^/]+\/\d+|[^/]+)$/.test(loc.pathname) && !loc.pathname.endsWith('/leetcodes'))
    || /\/checkpoint\//.test(loc.pathname)
    || /\/exam$/.test(loc.pathname)
  );

  const routeLevel = pathLevelId(loc.pathname);
  const csharpActive = !!routeLevel && (
    csharpLevels.some((l) => l.id === routeLevel) || /^s[a-z]$/.test(routeLevel)
  );
  const pythonActive = !!routeLevel && (
    levels.some((l) => l.id === routeLevel) || /^[a-z]$/.test(routeLevel)
  );
  const odooActive = !!routeLevel && (
    odooLevels.some((l) => l.id === routeLevel) || /^o[a-z]$/.test(routeLevel)
  );
  const hasActiveLanguage = csharpActive || pythonActive;

  useEffect(() => {
    setDrawerOpen(false);
  }, [loc.pathname]);

  useEffect(() => {
    if (csharpActive) {
      setLanguagesOpen(true);
      setCsharpOpen(true);
    }
    if (pythonActive) {
      setLanguagesOpen(true);
      setPythonOpen(true);
    }
    if (odooActive) setCompaniesOpen(true);
  }, [loc.pathname, csharpActive, pythonActive, odooActive]);

  useEffect(() => {
    api.curriculum()
      .then((c) => {
        const od = c.odoo_levels as CurriculumLevel[] | undefined;
        if (od?.length) setOdooLevels(od);
        const cs = c.csharp_levels as CurriculumLevel[] | undefined;
        if (cs?.length) setCsharpLevels(cs);
      })
      .catch(() => {});
  }, [locale]);

  useEffect(() => {
    api.returnExamStatus()
      .then(setReturnExam)
      .catch(() => {});
  }, [loc.pathname]);

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [drawerOpen]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrawerOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [drawerOpen]);

  const nav = (
    <SidebarNav
      t={t}
      levels={levels}
      csharpLevels={csharpLevels}
      odooLevels={odooLevels}
      languagesOpen={languagesOpen}
      csharpOpen={csharpOpen}
      pythonOpen={pythonOpen}
      companiesOpen={companiesOpen}
      onToggleLanguages={() => setLanguagesOpen((o) => !o)}
      onToggleCsharp={() => setCsharpOpen((o) => !o)}
      onTogglePython={() => setPythonOpen((o) => !o)}
      onToggleCompanies={() => setCompaniesOpen((o) => !o)}
      dashboardActive={loc.pathname === '/'}
      languagesActive={hasActiveLanguage}
      csharpActive={csharpActive}
      pythonActive={pythonActive}
      companiesActive={odooActive}
      leetcodesActive={isLeetcodesActive}
      projectsActive={isProjectsActive}
      orientadorActive={isOrientadorInsight}
      isLevelActive={isLevelActive}
    />
  );

  return (
    <div className="app-shell">
      <aside className="app-sidebar hidden md:flex">
        <SidebarBrand />
        {nav}
        <SidebarFooter settingsActive={isActive('/settings')} settingsLabel={t('common.settings')} />
      </aside>

      {drawerOpen && (
        <div className="app-drawer md:hidden">
          <button
            type="button"
            className="app-drawer-backdrop"
            aria-label={t('common.toggleMenu')}
            onClick={() => setDrawerOpen(false)}
          />
          <aside className="app-sidebar app-sidebar-drawer">
            <SidebarBrand />
            {nav}
            <SidebarFooter settingsActive={isActive('/settings')} settingsLabel={t('common.settings')} />
          </aside>
        </div>
      )}

      <div className="app-content">
        <header className="app-topbar md:hidden">
          <button
            type="button"
            className="rounded-xl p-2 text-text-muted transition hover:bg-surface-2 hover:text-text"
            onClick={() => setDrawerOpen((o) => !o)}
            aria-label={t('common.toggleMenu')}
            aria-expanded={drawerOpen}
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {drawerOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
          <SidebarBrand compact />
          <LanguageToggle compact />
        </header>

        {returnExam?.needed && loc.pathname !== '/return-exam' && (
          <div className="border-b border-amber-500/30 bg-amber-500/10">
            <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-5 py-2.5">
              <p className="text-sm text-amber-900">
                {t('returnExam.banner', { days: returnExam.inactivity_days || returnExam.threshold_days })}
              </p>
              <Link to="/return-exam" className="text-sm font-medium text-amber-900 underline-offset-2 hover:underline">
                {t('dashboard.returnExamStart')}
              </Link>
            </div>
          </div>
        )}

        <main className={`mx-auto px-5 py-8 md:px-8 ${isLeetcodeWorkspace ? 'max-w-[1920px]' : 'max-w-5xl'}`}>
          {children}
        </main>
      </div>

      <CodiCompanion />
    </div>
  );
}

function SidebarBrand({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className={`brand-mark shrink-0 ${compact ? '' : 'px-1 py-1.5'}`}>
      <span className="brand-mark-badge" aria-hidden>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M4 2h4v2.2H6.4C5.1 4.2 4.2 5.2 4.2 7S5.1 9.8 6.4 9.8H8V12H4c-2.2 0-3.6-1.8-3.6-5S1.8 2 4 2Z" fill="currentColor"/>
          <rect x="9.2" y="2" width="2.2" height="2.2" fill="currentColor"/>
          <rect x="12" y="2" width="2.2" height="2.2" fill="currentColor"/>
          <rect x="9.2" y="5" width="2.2" height="2.2" fill="currentColor"/>
        </svg>
      </span>
      <span className="flex flex-col">
        <span className="brand-mark-word">Codenda</span>
        {!compact && (
          <span className="mt-1 font-mono text-[10px] font-medium uppercase tracking-[0.16em] text-[#93c5fd]">
            SDE trainer
          </span>
        )}
      </span>
    </Link>
  );
}

function SidebarFooter({
  settingsActive,
  settingsLabel,
}: {
  settingsActive: boolean;
  settingsLabel: string;
}) {
  return (
    <div className="mt-auto space-y-1 border-t border-border pt-3">
      <SidebarLink to="/settings" label={settingsLabel} active={settingsActive} icon={<IconSettings />} />
      <div className="px-1 pt-1">
        <LanguageToggle compact tone="dark" />
      </div>
    </div>
  );
}

function SidebarNav({
  t,
  levels,
  csharpLevels,
  odooLevels,
  languagesOpen,
  csharpOpen,
  pythonOpen,
  companiesOpen,
  onToggleLanguages,
  onToggleCsharp,
  onTogglePython,
  onToggleCompanies,
  dashboardActive,
  languagesActive,
  csharpActive,
  pythonActive,
  companiesActive,
  leetcodesActive,
  projectsActive,
  orientadorActive,
  isLevelActive,
}: {
  t: (key: string, vars?: Record<string, string | number>) => string;
  levels: CurriculumLevel[];
  csharpLevels: CurriculumLevel[];
  odooLevels: CurriculumLevel[];
  languagesOpen: boolean;
  csharpOpen: boolean;
  pythonOpen: boolean;
  companiesOpen: boolean;
  onToggleLanguages: () => void;
  onToggleCsharp: () => void;
  onTogglePython: () => void;
  onToggleCompanies: () => void;
  dashboardActive: boolean;
  languagesActive: boolean;
  csharpActive: boolean;
  pythonActive: boolean;
  companiesActive: boolean;
  leetcodesActive: boolean;
  projectsActive: boolean;
  orientadorActive: boolean;
  isLevelActive: (id: string) => boolean;
}) {
  return (
    <nav className="app-sidebar-nav">
      <SidebarLink to="/" label={t('common.dashboard')} active={dashboardActive} icon={<IconHome />} />

      <SidebarSection
        label={t('common.languages')}
        open={languagesOpen}
        active={languagesActive}
        onToggle={onToggleLanguages}
        icon={<IconCode />}
      >
        <SidebarSection
          label={t('common.csharp')}
          open={csharpOpen}
          active={csharpActive}
          onToggle={onToggleCsharp}
          nested
        >
          {csharpLevels.length > 0 ? (
            csharpLevels.map((lvl) => (
              <SidebarLink
                key={lvl.id}
                to={`/${lvl.id}/roadmap`}
                label={trackLevelTitle(lvl, 'csharp', t)}
                active={isLevelActive(lvl.id)}
                nested
              />
            ))
          ) : (
            <p className="px-3 py-1.5 text-xs text-text-dim">{t('common.noLevels')}</p>
          )}
        </SidebarSection>
        <SidebarSection
          label={t('common.python')}
          open={pythonOpen}
          active={pythonActive}
          onToggle={onTogglePython}
          nested
        >
          {levels.map((lvl) => (
            <SidebarLink
              key={lvl.id}
              to={`/${lvl.id}/roadmap`}
              label={t('common.levelLetter', { letter: lvl.letter })}
              hint={lvl.title.replace(/^Level \w+ — /, '').replace(/^Nivel \w+ — /, '')}
              active={isLevelActive(lvl.id)}
              nested
            />
          ))}
        </SidebarSection>
      </SidebarSection>

      <SidebarLink to="/leetcodes" label={t('common.leetcodes')} active={leetcodesActive} icon={<IconHash />} />

      <SidebarSection
        label={t('common.companies')}
        open={companiesOpen}
        active={companiesActive}
        onToggle={onToggleCompanies}
        icon={<IconBuilding />}
      >
        {odooLevels.length > 0 ? (
          odooLevels.map((lvl) => (
            <SidebarLink
              key={lvl.id}
              to={`/${lvl.id}/roadmap`}
              label={trackLevelTitle(lvl, 'odoo', t)}
              active={isLevelActive(lvl.id)}
              nested
            />
          ))
        ) : (
          <p className="px-3 py-1.5 text-xs text-text-dim">{t('common.noLevels')}</p>
        )}
      </SidebarSection>

      <SidebarLink to="/stories" label={t('common.projects')} active={projectsActive} icon={<IconFolder />} />
      <SidebarLink to="/orientador" label={t('common.orientador')} active={orientadorActive} icon={<IconCompass />} />
    </nav>
  );
}

function SidebarSection({
  label,
  open,
  active,
  onToggle,
  icon,
  nested = false,
  children,
}: {
  label: string;
  open: boolean;
  active: boolean;
  onToggle: () => void;
  icon?: React.ReactNode;
  nested?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className={`sidebar-item ${nested ? 'sidebar-item-nested' : ''} ${active ? 'sidebar-item-active' : ''}`}
      >
        {icon && <span className="sidebar-icon">{icon}</span>}
        <span className="min-w-0 flex-1 truncate text-left">{label}</span>
        <svg
          className={`h-3.5 w-3.5 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className={nested ? 'sidebar-leaf' : 'sidebar-branch'}>{children}</div>}
    </div>
  );
}

function SidebarLink({
  to,
  label,
  hint,
  active,
  icon,
  nested = false,
}: {
  to: string;
  label: string;
  hint?: string;
  active: boolean;
  icon?: React.ReactNode;
  nested?: boolean;
}) {
  return (
    <Link
      to={to}
      className={`sidebar-item ${nested ? 'sidebar-item-nested' : ''} ${active ? 'sidebar-item-active' : ''}`}
    >
      {icon && <span className="sidebar-icon">{icon}</span>}
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {hint && <span className="sr-only">{hint}</span>}
    </Link>
  );
}

function IconHome() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5Z" />
    </svg>
  );
}

function IconCode() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m8 8-4 4 4 4M16 8l4 4-4 4M13 6l-2 12" />
    </svg>
  );
}

function IconHash() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 4 6 20M18 4l-2 16M4 9h16M3 15h16" />
    </svg>
  );
}

function IconBuilding() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 21V6a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v15M14 21V10h5a1 1 0 0 1 1 1v10M4 21h16M8 8h2M8 12h2M8 16h2M17 13h1M17 16h1" />
    </svg>
  );
}

function IconFolder() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7a1 1 0 0 1 1-1h5l2 2h7a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7Z" />
    </svg>
  );
}

function IconCompass() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
      <circle cx="12" cy="12" r="8" />
      <path strokeLinecap="round" strokeLinejoin="round" d="m14.8 9.2-1.2 4.4-4.4 1.2 1.2-4.4 4.4-1.2Z" />
    </svg>
  );
}

function IconSettings() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
      <circle cx="12" cy="12" r="3" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v1.6M12 17.9v1.6M4.5 12h1.6M17.9 12h1.6M6.4 6.4l1.1 1.1M16.5 16.5l1.1 1.1M17.6 6.4l-1.1 1.1M7.5 16.5l-1.1 1.1" />
    </svg>
  );
}
