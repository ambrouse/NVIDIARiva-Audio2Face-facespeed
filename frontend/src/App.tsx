import { useState } from 'react';
import { LogsPage } from './pages/LogsPage';
import { PipelinePage } from './pages/PipelinePage';
import { ServicesPage } from './pages/ServicesPage';
import { SystemPage } from './pages/SystemPage';
import './styles/app.css';

type Page = 'pipeline' | 'services' | 'logs' | 'system';

const navigation: { id: Page; label: string }[] = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'services', label: 'Services' },
  { id: 'logs', label: 'Logs' },
  { id: 'system', label: 'System' },
];

export function App() {
  const [page, setPage] = useState<Page>('pipeline');

  return (
    <main className="appShell">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="brand">
          <span className="brandMark">TSF</span>
          <div>
            <strong>Face Speed</strong>
            <p>Riva + Audio2Face</p>
          </div>
        </div>
        <nav>
          {navigation.map((item) => (
            <button className={page === item.id ? 'navItem active' : 'navItem'} key={item.id} onClick={() => setPage(item.id)}>
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <div className="content">
        {page === 'pipeline' && <PipelinePage />}
        {page === 'services' && <ServicesPage />}
        {page === 'logs' && <LogsPage />}
        {page === 'system' && <SystemPage />}
      </div>
    </main>
  );
}
