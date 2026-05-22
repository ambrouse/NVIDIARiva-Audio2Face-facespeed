import { useState } from 'react';
import { Activity, Database, MessageCircle, Settings, SlidersHorizontal } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { LogsPage } from './pages/LogsPage';
import { PipelinePage } from './pages/PipelinePage';
import { ServicesPage } from './pages/ServicesPage';
import { SystemPage } from './pages/SystemPage';
import './styles/app.css';

type Page = 'studio' | 'operations' | 'activity' | 'setup';

const navigation: { id: Page; label: string; Icon: LucideIcon }[] = [
  { id: 'studio', label: 'Voice', Icon: MessageCircle },
  { id: 'operations', label: 'Operations', Icon: Database },
  { id: 'activity', label: 'Activity', Icon: Activity },
  { id: 'setup', label: 'Setup', Icon: SlidersHorizontal },
];

export function App() {
  const [page, setPage] = useState<Page>('studio');

  return (
    <main className="appShell">
      <aside className="sideRail" aria-label="Primary">
        <div className="brand">
          <span className="brandMark">FS</span>
        </div>
        <nav className="railNav">
          {navigation.map((item) => (
            <button
              aria-label={item.label}
              title={item.label}
              className={page === item.id ? 'railItem active' : 'railItem'}
              key={item.id}
              onClick={() => setPage(item.id)}
            >
              <item.Icon size={20} strokeWidth={2.2} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <button className="railItem railSettings" aria-label="Settings" title="Settings" onClick={() => setPage('setup')}>
          <Settings size={20} strokeWidth={2.2} />
          <span>Settings</span>
        </button>
      </aside>
      <div className="content">
        {page === 'studio' && <PipelinePage />}
        {page === 'operations' && <ServicesPage />}
        {page === 'activity' && <LogsPage />}
        {page === 'setup' && <SystemPage />}
      </div>
    </main>
  );
}
