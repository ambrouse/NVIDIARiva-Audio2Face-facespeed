import { lazy, Suspense, FormEvent, useState } from 'react';

const FaceViewer = lazy(() => import('../components/FaceViewer').then((module) => ({ default: module.FaceViewer })));
import { createJob, Job } from '../services/api';

const jobStates = ['validating_text', 'generating_speech', 'speech_ready', 'sending_to_a2f', 'animating_face', 'completed'];

export function PipelinePage() {
  const [text, setText] = useState('Xin chào, đây là bản thử nghiệm Text to Speech to Face.');
  const [voice, setVoice] = useState('default');
  const [language, setLanguage] = useState('vi-VN');
  const [a2fProfile, setA2fProfile] = useState('default');
  const [outputMode, setOutputMode] = useState('preview');
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isInputInvalid = text.trim().length === 0 || text.length > 1000;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      setJob(await createJob({ text, voice, language, a2fProfile, outputMode }));
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
          <div className="titleRow">
            <p className="eyebrow">Pipeline</p>
            <span className="modeBadge">Local mock-safe</span>
          </div>
          <h1>Text → Speech → Face</h1>
          <p className="muted">Nhập text để chạy pipeline Riva TTS và Audio2Face; dashboard sẽ cập nhật trạng thái và preview 3D face.</p>
          <div className="notice">Frontend dùng localhost backend mặc định <code>127.0.0.1:8020</code>. NVIDIA thật chỉ chạy sau preflight và xác nhận.</div>
        </div>
        <form className="pipelineForm" onSubmit={handleSubmit}>
          <label htmlFor="text-input">Text input</label>
          <textarea id="text-input" value={text} onChange={(event) => setText(event.target.value)} rows={6} maxLength={1000} />
          <div className="formGrid">
            <label>
              Voice
              <input value={voice} onChange={(event) => setVoice(event.target.value)} />
            </label>
            <label>
              Language
              <input value={language} onChange={(event) => setLanguage(event.target.value)} />
            </label>
            <label>
              A2F profile
              <input value={a2fProfile} onChange={(event) => setA2fProfile(event.target.value)} />
            </label>
            <label>
              Output mode
              <select value={outputMode} onChange={(event) => setOutputMode(event.target.value)}>
                <option value="preview">preview</option>
                <option value="export">export</option>
                <option value="stream">stream</option>
              </select>
            </label>
          </div>
          <div className="formFooter">
            <span className={isInputInvalid ? 'limitText warnText' : 'limitText'}>{text.length}/1000 characters</span>
            <button type="submit" disabled={isLoading || isInputInvalid}>{isLoading ? 'Đang chạy...' : 'Run pipeline'}</button>
          </div>
        </form>
        {error && <div className="alert">{error}</div>}
        {job && (
          <>
            <div className="stateTimeline" aria-label="Job state timeline">
              {jobStates.map((state) => (
                <span className={job.state === state || job.state === 'completed' ? 'stateStep active' : 'stateStep'} key={state}>{state}</span>
              ))}
              {job.state === 'failed' && <span className="stateStep failed">failed</span>}
            </div>
            <div className="resultGrid" aria-live="polite">
              <div><strong>Job</strong><span>{job.id}</span></div>
              <div><strong>State</strong><span>{job.state}</span></div>
              <div><strong>Audio</strong><span>{job.audioPath ?? '-'}</span></div>
              <div><strong>Face result</strong><span>{job.resultPath ?? '-'}</span></div>
              {job.error && <div className="resultError"><strong>Error</strong><span>{job.error}</span></div>}
            </div>
          </>
        )}
      </div>
      <Suspense fallback={<div className="faceViewerCard">Loading 3D face viewer...</div>}>
        <FaceViewer isActive={job?.state === 'completed'} />
      </Suspense>
    </section>
  );
}
