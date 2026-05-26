import { useEffect, useState } from 'react';
import { fetchSystemChecks, SystemCheck } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function SystemPage() {
  const [checks, setChecks] = useState<SystemCheck[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSystemChecks().then(setChecks).catch((currentError: unknown) => {
      setError(currentError instanceof Error ? currentError.message : 'Unknown error');
    });
  }, []);

  return (
    <section className="supportPage">
      <div className="supportHeader">
        <p className="eyebrow">Setup</p>
        <h1>Machine readiness</h1>
      </div>
      {error && <div className="alert">{error}</div>}
      <div className="resourceGrid">
        <div><strong>Backend</strong><span>127.0.0.1:6320</span></div>
        <div><strong>Frontend</strong><span>127.0.0.1:6310</span></div>
        <div><strong>Riva</strong><span>127.0.0.1:6051</span></div>
        <div><strong>Audio2Face</strong><span>127.0.0.1:6040</span></div>
      </div>
      <div className="notice">Heavy NVIDIA actions are blocked unless ports, RAM, memory commit, disk, GPU/VRAM and Docker all pass the 10% reserve gates.</div>
      <div className="checkList">
        {checks.length === 0 && <div className="emptyState">No system checks loaded yet.</div>}
        {checks.map((check) => (
          <div className="checkRow" key={check.name}>
            <div>
              <strong>{check.name}</strong>
              <p className="muted">{check.detail}</p>
            </div>
            <StatusBadge healthy={check.ok} label={check.ok ? 'ok' : 'missing'} />
          </div>
        ))}
      </div>
      <div className="commandList">
        <p className="muted commandHint">Safe preflight commands for the target Linux host:</p>
        <code>bash scripts/setup.sh --check-ports</code>
        <code>bash scripts/setup.sh --check-resources</code>
        <code>bash scripts/setup.sh --check-gpu-light</code>
        <code>bash scripts/setup.sh --check-docker-space</code>
        <code>bash scripts/setup.sh --dry-run-nvidia-full</code>
      </div>
    </section>
  );
}
