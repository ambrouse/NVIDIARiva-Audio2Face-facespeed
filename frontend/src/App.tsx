import { useState } from 'react';
import { LogsPage } from './pages/LogsPage';
import { PipelinePage } from './pages/PipelinePage';
import { ServicesPage } from './pages/ServicesPage';
import { SystemPage } from './pages/SystemPage';
import './styles/app.css';

type Page = 'studio' | 'operations' | 'activity' | 'setup';

const navigation: { id: Page; label: string }[] = [
  { id: 'studio', label: 'Studio' },
  { id: 'operations', label: 'Operations' },
  { id: 'activity', label: 'Activity' },
  { id: 'setup', label: 'Setup' },
];

export function App() {
  const [page, setPage] = useState<Page>('studio');

  return (
    <main className="appShell">
      <header className="topBar">
        <div className="brand">
          <span className="brandMark">FS</span>
          <div>
            <strong>FaceSpeed Studio</strong>
            <p>Riva voice to talking 3D avatar</p>
          </div>
        </div>
        <nav className="topNav" aria-label="Primary">
          {navigation.map((item) => (
            <button className={page === item.id ? 'navItem active' : 'navItem'} key={item.id} onClick={() => setPage(item.id)}>
              {item.label}
            </button>
          ))}
        </nav>
      </header>
      <div className="content">
        {page === 'studio' && <PipelinePage />}
        {page === 'operations' && <ServicesPage />}
        {page === 'activity' && <LogsPage />}
        {page === 'setup' && <SystemPage />}
      </div>
    </main>
  );
}
