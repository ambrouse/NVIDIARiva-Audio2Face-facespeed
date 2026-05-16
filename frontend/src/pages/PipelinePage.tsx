import { lazy, Suspense, FormEvent, useState } from 'react';

const FaceViewer = lazy(() => import('../components/FaceViewer').then((module) => ({ default: module.FaceViewer })));
import { createJob, Job } from '../services/api';

export function PipelinePage() {
  const [text, setText] = useState('Xin chào, đây là bản thử nghiệm Text to Speech to Face.');
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      setJob(await createJob(text));
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="pipelineLayout">
      <div className="panel heroPanel">
        <div>
          <p className="eyebrow">Pipeline</p>
          <h1>Text → Speech → Face</h1>
          <p className="muted">Nhập text để chạy pipeline Riva TTS và Audio2Face; dashboard sẽ cập nhật trạng thái và preview 3D face.</p>
        </div>
        <form className="pipelineForm" onSubmit={handleSubmit}>
          <label htmlFor="text-input">Text input</label>
          <textarea id="text-input" value={text} onChange={(event) => setText(event.target.value)} rows={6} />
          <button type="submit" disabled={isLoading || text.trim().length === 0}>{isLoading ? 'Đang chạy...' : 'Run pipeline'}</button>
        </form>
        {error && <div className="alert">{error}</div>}
        {job && (
          <div className="resultGrid" aria-live="polite">
            <div><strong>Job</strong><span>{job.id}</span></div>
            <div><strong>State</strong><span>{job.state}</span></div>
            <div><strong>Audio</strong><span>{job.audioPath ?? '-'}</span></div>
            <div><strong>Face result</strong><span>{job.resultPath ?? '-'}</span></div>
          </div>
        )}
      </div>
      <Suspense fallback={<div className="faceViewerCard">Loading 3D face viewer...</div>}>
        <FaceViewer isActive={job?.state === 'completed'} />
      </Suspense>
    </section>
  );
}
