import { useState } from 'react';
import { fetchServiceLogs } from '../services/api';

const services = ['riva', 'audio2face', 'backend-worker'];

export function LogsPage() {
  const [selectedService, setSelectedService] = useState('riva');
  const [logs, setLogs] = useState<string[]>([]);
  const [filter, setFilter] = useState('');

  async function handleLoadLogs() {
    setLogs(await fetchServiceLogs(selectedService));
  }

  const filteredLogs = logs.filter((line) => line.toLowerCase().includes(filter.toLowerCase()));

  return (
    <section className="supportPage">
      <div className="supportHeader">
        <p className="eyebrow">Activity</p>
        <h1>Service logs</h1>
      </div>
      <div className="toolbar">
        <select value={selectedService} onChange={(event) => setSelectedService(event.target.value)} aria-label="Service">
          {services.map((service) => <option key={service} value={service}>{service}</option>)}
        </select>
        <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter logs" />
        <button onClick={() => void handleLoadLogs()}>Load logs</button>
      </div>
      <pre className="logViewer">{filteredLogs.length > 0 ? filteredLogs.join('\n') : 'No logs loaded.'}</pre>
    </section>
  );
}
