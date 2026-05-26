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
      state: status.qdrantAvailable ? 'graph' : 'local',
      healthy: true,
      detail: status.embeddingBaseUrl,
      meta: [
        ['Provider', status.retrievalProvider],
        ['Qdrant', status.qdrantAvailable ? 'ready on 6002' : 'not connected'],
      ],
    },
    {
      name: 'Postgres ledger',
      state: status.postgresAvailable ? 'ready' : 'blocked',
      healthy: status.postgresAvailable,
      detail: status.postgresAvailable ? 'Agent session, task, history and prompt tables are online.' : 'Postgres DSN is not reachable.',
      meta: [
        ['Port', '127.0.0.1:6001'],
        ['Mode', 'session memory'],
      ],
    },
    {
      name: 'LLM reasoning',
      state: status.llmAvailable ? 'ready' : 'blocked',
      healthy: status.llmAvailable,
      detail: status.llmAvailable ? 'OpenAI-compatible LLM is reachable.' : 'LLM teacher/review is unavailable; benchmark pass is blocked.',
      meta: [
        ['Provider', 'vllm / openai-compatible'],
        ['Graph RAG', status.graphRagEnabled ? 'enabled' : 'disabled'],
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
