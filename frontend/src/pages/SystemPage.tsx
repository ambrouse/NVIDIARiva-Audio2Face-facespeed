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
    <section className="panel">
      <p className="eyebrow">Setup</p>
      <h2>Hardware and software checks</h2>
      {error && <div className="alert">{error}</div>}
      <div className="checkList">
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
      <p className="muted commandHint">Run <code>./scripts/setup.sh --check</code> on the target Linux host for the full NVIDIA setup report.</p>
    </section>
  );
}
