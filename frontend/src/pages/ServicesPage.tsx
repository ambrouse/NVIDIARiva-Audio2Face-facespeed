import { useEffect, useState } from 'react';
import { fetchServices, ServiceStatus } from '../services/api';
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

  useEffect(() => {
    void loadServices();
  }, []);

  return (
    <section className="supportPage">
      <div className="supportHeader">
        <p className="eyebrow">Operations</p>
        <h1>Runtime services</h1>
        <p className="muted">Project-scoped service state and container ownership.</p>
        <button className="secondary compactButton" onClick={() => void loadServices()}>Refresh</button>
      </div>
      {error && <div className="alert">{error}</div>}
      <div className="cards">
        {services.map((service) => (
          <article className="serviceCard" key={service.name}>
            <div className="cardHeader">
              <h3>{service.name}</h3>
              <StatusBadge healthy={service.healthy} label={service.state} />
            </div>
            <p className="muted">{service.detail}</p>
            <dl className="serviceMeta">
              <div>
                <dt>Mode</dt>
                <dd>{service.managerMode}</dd>
              </div>
              <div>
                <dt>Container</dt>
                <dd>{service.containerName ?? 'not configured'}</dd>
              </div>
              <div>
                <dt>Docker state</dt>
                <dd>{service.containerStatus ?? 'not found'}</dd>
              </div>
              {service.containerImage && (
                <div>
                  <dt>Image</dt>
                  <dd>{service.containerImage}</dd>
                </div>
              )}
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
