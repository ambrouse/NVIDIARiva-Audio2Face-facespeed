import { useEffect, useState } from 'react';
import { Save, RefreshCw } from 'lucide-react';
import { fetchPrompts, PromptConfig, updatePrompt } from '../services/api';

export function PromptsPage() {
  const [prompts, setPrompts] = useState<PromptConfig[]>([]);
  const [drafts, setDrafts] = useState<Record<string, PromptConfig>>({});
  const [busyAgent, setBusyAgent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadPrompts() {
    try {
      const nextPrompts = await fetchPrompts();
      setPrompts(nextPrompts);
      setDrafts(Object.fromEntries(nextPrompts.map((prompt) => [prompt.agent, prompt])));
      setError(null);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Cannot load prompts');
    }
  }

  useEffect(() => {
    void loadPrompts();
  }, []);

  async function savePrompt(agent: string) {
    const draft = drafts[agent];
    if (!draft) {
      return;
    }
    setBusyAgent(agent);
    try {
      const saved = await updatePrompt(agent, { name: draft.name, content: draft.content, enabled: draft.enabled });
      setPrompts((current) => current.map((prompt) => prompt.agent === agent ? saved : prompt));
      setDrafts((current) => ({ ...current, [agent]: saved }));
      setError(null);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Cannot save prompt');
    } finally {
      setBusyAgent(null);
    }
  }

  function patchDraft(agent: string, patch: Partial<PromptConfig>) {
    setDrafts((current) => ({ ...current, [agent]: { ...current[agent], ...patch } }));
  }

  return (
    <section className="supportPage promptPage">
      <div className="supportHeader">
        <p className="eyebrow">Prompts</p>
        <h1>Agent prompt manager</h1>
        <button className="secondary compactButton" type="button" onClick={() => void loadPrompts()}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>
      {error && <div className="alert">{error}</div>}
      <div className="promptGrid">
        {prompts.map((prompt) => {
          const draft = drafts[prompt.agent] ?? prompt;
          return (
            <article className="promptCard" key={prompt.agent}>
              <div className="cardHeader">
                <div>
                  <p className="eyebrow">{prompt.agent}</p>
                  <input aria-label={`${prompt.agent} prompt name`} value={draft.name} onChange={(event) => patchDraft(prompt.agent, { name: event.target.value })} />
                </div>
                <label className="toggleLine">
                  <input type="checkbox" checked={draft.enabled} onChange={(event) => patchDraft(prompt.agent, { enabled: event.target.checked })} />
                  <span>enabled</span>
                </label>
              </div>
              <textarea aria-label={`${prompt.agent} prompt content`} value={draft.content} onChange={(event) => patchDraft(prompt.agent, { content: event.target.value })} />
              <div className="promptFooter">
                <span>{draft.updatedAt ? new Date(draft.updatedAt).toLocaleString() : 'local default'}</span>
                <button className="iconButton secondary" type="button" aria-label={`Save ${prompt.agent} prompt`} disabled={busyAgent === prompt.agent} onClick={() => void savePrompt(prompt.agent)}>
                  <Save size={17} />
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
