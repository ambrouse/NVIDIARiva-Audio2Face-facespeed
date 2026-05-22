import { useEffect, useState } from 'react';
import { fetchRagStatus, RagRuntimeStatus } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function ServicesPage() {
  const [status, setStatus] = useState<RagRuntimeStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadRuntime() {
    try {
      setStatus(await fetchRagStatus());
      setError(null);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Unknown error');
    }
  }

  useEffect(() => {
    void loadRuntime();
  }, []);

  const runtimeCards = status ? [
    {
      name: 'Riva ASR',
      state: status.asrAvailable ? 'ready' : 'blocked',
      healthy: status.asrAvailable,
      detail: status.asrDetail,
      meta: [
        ['Provider', 'riva-asr'],
        ['Languages', status.languages.join(', ')],
      ],
    },
    {
      name: 'Docling parse',
      state: 'ready',
      healthy: true,
      detail: status.doclingBaseUrl,
      meta: [
        ['Provider', status.parseProvider],
        ['Mode', 'main path'],
      ],
    },
    {
      name: 'Embedding rerank',
      state: 'ready',
      healthy: true,
      detail: status.embeddingBaseUrl,
      meta: [
        ['Provider', status.retrievalProvider],
        ['Mode', 'main path'],
      ],
    },
    {
      name: 'Knowledge index',
      state: status.documentCount > 0 ? 'ready' : 'empty',
      healthy: status.documentCount > 0,
      detail: `${status.documentCount} documents / ${status.chunkCount} chunks`,
      meta: [
        ['Source', 'uploaded PDFs'],
        ['Fallback', 'disabled'],
      ],
    },
  ] : [];

  return (
    <section className="supportPage">
      <div className="supportHeader">
        <p className="eyebrow">Operations</p>
        <h1>Runtime services</h1>
        <button className="secondary compactButton" onClick={() => void loadRuntime()}>Refresh</button>
      </div>
      {error && <div className="alert">{error}</div>}
      <div className="cards">
        {runtimeCards.map((service) => (
          <article className="serviceCard" key={service.name}>
            <div className="cardHeader">
              <h3>{service.name}</h3>
              <StatusBadge healthy={service.healthy} label={service.state} />
            </div>
            <p className="muted">{service.detail}</p>
            <dl className="serviceMeta">
              {service.meta.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
