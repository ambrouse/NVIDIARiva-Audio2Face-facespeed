import { FormEvent, useState } from 'react';

import { FaceViewer } from '../components/FaceViewer';
import { createJob, Job, resolveApiUrl } from '../services/api';

const jobStates = ['validating_text', 'generating_speech', 'speech_ready', 'sending_to_a2f', 'animating_face', 'completed'];
const sampleText = 'Hello, I am your real-time 3D speaking avatar. This demo uses NVIDIA Riva speech and a browser ARKit face rig.';

export function PipelinePage() {
  const [text, setText] = useState(sampleText);
  const [voice, setVoice] = useState('English-US.Female-1');
  const [language, setLanguage] = useState('en-US');
  const [a2fProfile, setA2fProfile] = useState('default');
  const [outputMode, setOutputMode] = useState('preview');
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isInputInvalid = text.trim().length === 0 || text.length > 1000;
  const resolvedAudioUrl = job?.audioUrl ? resolveApiUrl(job.audioUrl) : null;
  const resolvedAnimationUrl = job?.animationUrl ? resolveApiUrl(job.animationUrl) : null;

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
    <section className="studioLayout">
      <div className="studioMain">
        <section className="studioComposer" aria-labelledby="studio-title">
          <div className="studioIntro">
            <p className="eyebrow">Avatar Studio</p>
            <h1 id="studio-title">Create a speaking 3D avatar</h1>
            <p className="muted">Generate English speech with Riva and preview the synchronized 3D face in the browser.</p>
          </div>

          <form className="pipelineForm" onSubmit={handleSubmit}>
            <div className="scriptHeader">
              <label htmlFor="text-input">Script</label>
              <button className="textButton" type="button" onClick={() => setText(sampleText)}>Use sample</button>
            </div>
            <textarea id="text-input" value={text} onChange={(event) => setText(event.target.value)} rows={8} maxLength={1000} />

            <div className="controlGrid">
              <label>
                Voice
                <select value={voice} onChange={(event) => setVoice(event.target.value)}>
                  <option value="English-US.Female-1">English-US.Female-1</option>
                  <option value="English-US.Male-1">English-US.Male-1</option>
                  <option value="default">default</option>
                </select>
              </label>
              <label>
                Language
                <select value={language} onChange={(event) => setLanguage(event.target.value)}>
                  <option value="en-US">en-US</option>
                </select>
              </label>
              <label>
                Avatar rig
                <select value={a2fProfile} onChange={(event) => setA2fProfile(event.target.value)}>
                  <option value="default">ReadyPlayer ARKit</option>
                  <option value="james">NVIDIA James fallback</option>
                </select>
              </label>
              <label>
                Output
                <select value={outputMode} onChange={(event) => setOutputMode(event.target.value)}>
                  <option value="preview">Preview</option>
                  <option value="export">Export artifact</option>
                  <option value="stream">Stream-ready</option>
                </select>
              </label>
            </div>

            <div className="formFooter">
              <span className={isInputInvalid ? 'limitText warnText' : 'limitText'}>{text.length}/1000 characters</span>
              <button className="primaryAction" type="submit" disabled={isLoading || isInputInvalid}>{isLoading ? 'Generating...' : 'Generate avatar speech'}</button>
            </div>
          </form>

          {error && <div className="alert">{error}</div>}
        </section>

        {job && (
          <section className="outputPanel" aria-label="Generation output">
            <div className="outputHeader">
              <div>
                <p className="eyebrow">Output</p>
                <h2>{job.state === 'completed' ? 'Speech ready' : 'Generating speech'}</h2>
              </div>
              <span className={job.state === 'completed' ? 'badge badgeOk' : 'badge badgeWarn'}>{job.state}</span>
            </div>

            <div className="stateTimeline" aria-label="Generation state timeline">
              {jobStates.map((state) => (
                <span className={job.state === state || job.state === 'completed' ? 'stateStep active' : 'stateStep'} key={state}>{state}</span>
              ))}
              {job.state === 'failed' && <span className="stateStep failed">failed</span>}
            </div>

            <div className="resultGrid compact" aria-live="polite">
              <div><strong>Job</strong><span>{job.id}</span></div>
              <div>
                <strong>Audio</strong>
                {resolvedAudioUrl ? <audio controls src={resolvedAudioUrl} /> : <span>{job.audioPath ?? '-'}</span>}
              </div>
              <div>
                <strong>Animation</strong>
                {resolvedAnimationUrl ? <a href={resolvedAnimationUrl} target="_blank" rel="noreferrer">browser-viseme JSON</a> : <span>{job.resultPath ?? '-'}</span>}
              </div>
              {job.error && <div className="resultError"><strong>Error</strong><span>{job.error}</span></div>}
            </div>
          </section>
        )}
      </div>

      <aside className="studioPreview" aria-label="3D avatar preview">
        <FaceViewer isReady={job?.state === 'completed'} audioUrl={resolvedAudioUrl} animationUrl={resolvedAnimationUrl} />
      </aside>
    </section>
  );
}
