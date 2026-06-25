import { Link, useLocation } from 'react-router-dom';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/kumon', label: 'Kumon' },
  { to: '/leetcode', label: 'LeetCode' },
  { to: '/interview', label: 'Interview' },
  { to: '/odoo', label: 'Odoo' },
  { to: '/settings', label: 'Settings' },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700 bg-slate-900/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-emerald-400">PythonOS</span>
            <span className="text-xs text-slate-500">Kumon × LeetCode × Odoo</span>
          </div>
          <nav className="flex gap-1">
            {links.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className={`rounded-lg px-3 py-1.5 text-sm transition ${
                  loc.pathname === l.to
                    ? 'bg-emerald-600/20 text-emerald-400'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
