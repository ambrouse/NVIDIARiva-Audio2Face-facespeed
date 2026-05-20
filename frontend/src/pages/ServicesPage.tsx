import { useEffect, useState } from 'react';
import { fetchServices, runServiceAction, ServiceStatus } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function ServicesPage() {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadServices() {
    try {
      setServices(await fetchServices());
      setError(null);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Unknown error');
    }
  }

  async function handleAction(serviceName: string, action: 'start' | 'stop' | 'restart') {
    const confirmed = window.confirm(`${action} ${serviceName}? Only project-scoped/local mock actions should run from this dashboard.`);
    if (!confirmed) {
      return;
    }
    await runServiceAction(serviceName, action);
    await loadServices();
  }

  useEffect(() => {
    void loadServices();
  }, []);

  return (
    <section className="panel">
      <p className="eyebrow">Control plane</p>
      <h2>Service dashboard</h2>
      {error && <div className="alert">{error}</div>}
      <div className="cards">
        {services.map((service) => (
          <article className="serviceCard" key={service.name}>
            <div className="cardHeader">
              <h3>{service.name}</h3>
              <StatusBadge healthy={service.healthy} label={service.state} />
            </div>
            <p className="muted">{service.detail}</p>
            <div className="actions">
              <button onClick={() => void handleAction(service.name, 'start')}>Start</button>
              <button onClick={() => void handleAction(service.name, 'restart')}>Restart</button>
              <button className="secondary" onClick={() => void handleAction(service.name, 'stop')}>Stop</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
