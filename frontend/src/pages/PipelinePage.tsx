import { ChangeEvent, PointerEvent, useEffect, useMemo, useRef, useState } from 'react';
import {
  Bot,
  Check,
  Database,
  FileUp,
  Mic,
  Pencil,
  RefreshCw,
  Save,
  Send,
  Sparkles,
  Trash2,
  Waypoints,
  User,
  X,
} from 'lucide-react';

import { AgentTraceCanvas } from '../components/AgentTraceCanvas';
import { FaceViewer } from '../components/FaceViewer';
import {
  AgentSessionStatus,
  createVoiceTurn,
  deleteDocument,
  fetchAgentSession,
  fetchDocuments,
  fetchRagStatus,
  RagDocument,
  RagRuntimeStatus,
  resolveApiUrl,
  transcribeVoice,
  updateDocument,
  uploadDocument,
  VoiceTurn,
} from '../services/api';

type RecordingState = 'idle' | 'recording' | 'transcribing';
type DialogName = 'sources' | 'runtime' | 'trace' | 'avatar' | null;
type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  citations?: VoiceTurn['answer']['citations'];
};
type FaceModelOption = {
  id: string;
  label: string;
  asset: string;
  expression: number;
  scale: number;
};

const faceModels: FaceModelOption[] = [
  { id: 'atlas', label: 'Atlas', asset: '/models/readyplayer-talk-arkit.glb', expression: 0.78, scale: 1.08 },
  { id: 'atlas-calm', label: 'Atlas calm', asset: '/models/readyplayer-talk-arkit.glb', expression: 0.48, scale: 1.0 },
  { id: 'atlas-close', label: 'Atlas close', asset: '/models/readyplayer-talk-arkit.glb', expression: 0.92, scale: 1.22 },
];

export function PipelinePage() {
  const [status, setStatus] = useState<RagRuntimeStatus | null>(null);
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [language, setLanguage] = useState('en-US');
  const [voice, setVoice] = useState('English-US.Female-1');
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [turn, setTurn] = useState<VoiceTurn | null>(null);
  const [activeSession, setActiveSession] = useState<AgentSessionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documentDrafts, setDocumentDrafts] = useState<Record<string, { title: string; summary: string; language: string }>>({});
  const [busyDocumentId, setBusyDocumentId] = useState<string | null>(null);
  const [editingDocumentId, setEditingDocumentId] = useState<string | null>(null);
  const [isAnswering, setIsAnswering] = useState(false);
  const [dialog, setDialog] = useState<DialogName>(null);
  const [selectedModelId, setSelectedModelId] = useState(faceModels[0].id);
  const [faceScale, setFaceScale] = useState(faceModels[0].scale);
  const [expressionIntensity, setExpressionIntensity] = useState(faceModels[0].expression);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatHistoryRef = useRef<HTMLDivElement | null>(null);

  const selectedModel = useMemo(
    () => faceModels.find((model) => model.id === selectedModelId) ?? faceModels[0],
    [selectedModelId],
  );
  const resolvedAudioUrl = turn?.audioUrl ? resolveApiUrl(turn.audioUrl) : null;
  const resolvedAnimationUrl = turn?.animationUrl ? resolveApiUrl(turn.animationUrl) : null;
  const canSubmit = draft.trim().length > 0 && documents.length > 0 && recordingState === 'idle' && !isAnswering;

  useEffect(() => {
    void refreshRuntime();
  }, []);

  useEffect(() => {
    const history = chatHistoryRef.current;
    if (!history) {
      return;
    }
    if (typeof history.scrollTo === 'function') {
      history.scrollTo({ top: history.scrollHeight, behavior: 'smooth' });
    } else {
      history.scrollTop = history.scrollHeight;
    }
  }, [messages, isAnswering]);

  useEffect(() => {
    if (!isAnswering || !activeSession?.sessionId) {
      return;
    }
    let cancelled = false;
    const interval = window.setInterval(() => {
      fetchAgentSession(activeSession.sessionId)
        .then((nextStatus) => {
          if (!cancelled) {
            setActiveSession(nextStatus);
          }
        })
        .catch(() => undefined);
    }, 800);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [activeSession?.sessionId, isAnswering]);

  async function refreshRuntime() {
    const [nextStatus, nextDocuments] = await Promise.all([fetchRagStatus(), fetchDocuments()]);
    setStatus(nextStatus);
    setDocuments(nextDocuments);
    setDocumentDrafts((current) => {
      const next: Record<string, { title: string; summary: string; language: string }> = {};
      nextDocuments.forEach((document) => {
        next[document.id] = current[document.id] ?? {
          title: document.title,
          summary: document.summary,
          language: document.language,
        };
      });
      return next;
    });
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setIsUploading(true);
    setError(null);
    try {
      await uploadDocument(file, language);
      await refreshRuntime();
      setDialog('sources');
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  }

  async function saveDocument(document: RagDocument) {
    const draft = documentDrafts[document.id];
    if (!draft) {
      return;
    }
    setBusyDocumentId(document.id);
    setError(null);
    try {
      await updateDocument(document.id, {
        title: draft.title,
        summary: draft.summary,
        language: draft.language,
      });
      setEditingDocumentId(null);
      await refreshRuntime();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Update failed');
    } finally {
      setBusyDocumentId(null);
    }
  }

  async function removeDocument(document: RagDocument) {
    setBusyDocumentId(document.id);
    setError(null);
    try {
      await deleteDocument(document.id);
      setMessages((current) => current.filter((message) => !message.citations?.some((citation) => citation.documentId === document.id)));
      if (turn?.answer.citations.some((citation) => citation.documentId === document.id)) {
        setTurn(null);
      }
      setEditingDocumentId(null);
      await refreshRuntime();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Delete failed');
    } finally {
      setBusyDocumentId(null);
    }
  }

  function updateDocumentDraft(documentId: string, patch: Partial<{ title: string; summary: string; language: string }>) {
    setDocumentDrafts((current) => ({
      ...current,
      [documentId]: {
        title: current[documentId]?.title ?? '',
        summary: current[documentId]?.summary ?? '',
        language: current[documentId]?.language ?? language,
        ...patch,
      },
    }));
  }

  async function handleVoicePressStart(event: PointerEvent<HTMLButtonElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    if (recordingState !== 'idle' || isAnswering) {
      return;
    }
    await startRecording();
  }

  function handleVoicePressEnd() {
    if (recordingState === 'recording') {
      recorderRef.current?.stop();
      setRecordingState('transcribing');
    }
  }

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/ogg;codecs=opus') ? 'audio/ogg;codecs=opus' : '';
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        try {
          const audio = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
          const result = await transcribeVoice(audio);
          setDraft(result.text);
          await submitMessage(result.text);
        } catch (currentError) {
          setError(currentError instanceof Error ? currentError.message : 'Transcription failed');
        } finally {
          setRecordingState('idle');
        }
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecordingState('recording');
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Microphone permission was denied');
      setRecordingState('idle');
    }
  }

  async function submitMessage(rawMessage = draft) {
    const message = rawMessage.trim();
    if (!message || isAnswering) {
      return;
    }
    if (documents.length === 0) {
      setError('Upload a PDF source before asking.');
      setDialog('sources');
      return;
    }

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: 'user', text: message };
    const sessionId = crypto.randomUUID();
    setActiveSession({ sessionId, state: 'running', question: message, answer: '', events: [] });
    setMessages((current) => [...current, userMessage]);
    setDraft('');
    setIsAnswering(true);
    setError(null);
    try {
      const nextTurn = await createVoiceTurn({ message, language, voice, outputMode: 'preview', sessionId });
      setTurn(nextTurn);
      setActiveSession({ sessionId: nextTurn.sessionId ?? sessionId, state: 'completed', question: message, answer: nextTurn.answer.text, events: nextTurn.agentEvents });
      setMessages((current) => [
        ...current,
        {
          id: nextTurn.id,
          role: 'assistant',
          text: nextTurn.answer.text,
          citations: nextTurn.answer.citations,
        },
      ]);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : 'Voice turn failed');
    } finally {
      setIsAnswering(false);
    }
  }

  function handleModelChange(modelId: string) {
    const nextModel = faceModels.find((model) => model.id === modelId) ?? faceModels[0];
    setSelectedModelId(nextModel.id);
    setFaceScale(nextModel.scale);
    setExpressionIntensity(nextModel.expression);
  }

  return (
    <section className="voiceProduct">
      <input ref={fileInputRef} className="hiddenInput" type="file" accept="application/pdf,.pdf" onChange={handleUpload} disabled={isUploading} />

      <div className="chatPane">
        <header className="productHeader">
          <div>
            <p className="eyebrow">FaceSpeed</p>
            <h1>Voice RAG</h1>
          </div>
          <div className="headerActions">
            <button className="iconTool" type="button" aria-label="Sources" title="Sources" onClick={() => setDialog('sources')}>
              <Database size={18} />
              <span>{documents.length}</span>
            </button>
            <button className="iconTool" type="button" aria-label="Runtime" title="Runtime" onClick={() => setDialog('runtime')}>
              <Sparkles size={18} />
              <span>{status?.asrAvailable ? 'on' : 'off'}</span>
            </button>
            <button className="iconTool" type="button" aria-label="Trace" title="Trace" onClick={() => setDialog('trace')} disabled={!turn}>
              <Waypoints size={18} />
            </button>
          </div>
        </header>

        <div className="chatHistory" ref={chatHistoryRef} aria-label="Chat history">
          {messages.length === 0 ? (
            <div className="emptyConversation">
              <Bot size={26} />
              <span>Hold to talk</span>
            </div>
          ) : (
            messages.map((message) => (
              <article className={`chatMessage ${message.role}`} key={message.id}>
                <div className="messageIcon" aria-hidden="true">
                  {message.role === 'user' ? <User size={17} /> : <Bot size={17} />}
                </div>
                <div>
                  <p>{message.text}</p>
                  {message.citations?.length ? (
                    <div className="citationList" aria-label="Answer citations">
                      {message.citations.map((citation) => (
                        <button key={citation.chunkId} type="button" onClick={() => setDialog('sources')}>
                          {citation.source} p.{citation.page}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              </article>
            ))
          )}
          {isAnswering && (
            <article className="chatMessage assistant thinking">
              <div className="messageIcon" aria-hidden="true"><Bot size={17} /></div>
              <div><p>Thinking...</p></div>
            </article>
          )}
        </div>

        {error && <div className="alert">{error}</div>}

        <footer className="voiceDock">
          <button
            className={recordingState === 'recording' ? 'voiceButton recording' : 'voiceButton'}
            type="button"
            aria-label="Hold to talk"
            title="Hold to talk"
            onPointerDown={(event) => void handleVoicePressStart(event)}
            onPointerUp={handleVoicePressEnd}
            onPointerCancel={handleVoicePressEnd}
            onPointerLeave={handleVoicePressEnd}
            disabled={recordingState === 'transcribing' || isAnswering}
          >
            <Mic size={28} />
          </button>
          <div className="composer">
            <input
              aria-label="Message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={recordingState === 'transcribing' ? 'Transcribing...' : 'Ask from your PDFs'}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  void submitMessage();
                }
              }}
            />
            <button className="sendButton" type="button" aria-label="Send message" onClick={() => void submitMessage()} disabled={!canSubmit}>
              <Send size={18} />
            </button>
          </div>
        </footer>
      </div>

      <aside className="avatarPane">
        <FaceViewer
          isReady={turn?.answer.reviewStatus === 'pass'}
          audioUrl={resolvedAudioUrl}
          animationUrl={resolvedAnimationUrl}
          modelUrl={selectedModel.asset}
          modelLabel={selectedModel.label}
          faceScale={faceScale}
          expressionIntensity={expressionIntensity}
          onOpenSettings={() => setDialog('avatar')}
        />
      </aside>

      {dialog && (
        <div className="modalBackdrop" role="presentation" onClick={() => setDialog(null)}>
          <section className="modalPanel" role="dialog" aria-modal="true" aria-label={`${dialog} dialog`} onClick={(event) => event.stopPropagation()}>
            <div className="modalHeader">
              <div>
                <p className="eyebrow">{dialog}</p>
                <h2>{dialogTitle(dialog)}</h2>
              </div>
              <button className="iconButton secondary" type="button" aria-label="Close dialog" onClick={() => setDialog(null)}>
                <X size={18} />
              </button>
            </div>

            {dialog === 'sources' && (
              <div className="documentList">
                <div className="sourceToolbar">
                  <button className="uploadButton" type="button" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
                    <FileUp size={18} />
                    {isUploading ? 'Indexing PDF' : 'Upload PDF'}
                  </button>
                  <button className="iconButton secondary" type="button" aria-label="Refresh sources" title="Refresh sources" onClick={() => void refreshRuntime()}>
                    <RefreshCw size={18} />
                  </button>
                </div>
                {documents.length ? documents.map((document) => (
                  <article className="documentItem" id={`doc-${document.id}`} key={document.id}>
                    {editingDocumentId === document.id ? (
                      <div className="documentEditor">
                        <label>
                          <span>Title</span>
                          <input value={documentDrafts[document.id]?.title ?? document.title} onChange={(event) => updateDocumentDraft(document.id, { title: event.target.value })} />
                        </label>
                        <label>
                          <span>Summary</span>
                          <textarea value={documentDrafts[document.id]?.summary ?? document.summary} onChange={(event) => updateDocumentDraft(document.id, { summary: event.target.value })} />
                        </label>
                        <label>
                          <span>Language</span>
                          <select value={documentDrafts[document.id]?.language ?? document.language} onChange={(event) => updateDocumentDraft(document.id, { language: event.target.value })}>
                            <option value="en-US">English</option>
                            <option value="vi-VN">Vietnamese</option>
                          </select>
                        </label>
                      </div>
                    ) : (
                      <>
                        <strong>{document.title}</strong>
                        <span>{document.filename} - {document.language} - {document.pageCount} page - {document.chunkCount} chunks</span>
                        <p>{document.summary || 'Indexed and ready for retrieval.'}</p>
                      </>
                    )}
                    <div className="documentActions">
                      {editingDocumentId === document.id ? (
                        <button className="iconButton secondary" type="button" aria-label={`Save ${document.filename}`} title="Save" disabled={busyDocumentId === document.id} onClick={() => void saveDocument(document)}>
                          <Save size={17} />
                        </button>
                      ) : (
                        <button className="iconButton secondary" type="button" aria-label={`Edit ${document.filename}`} title="Edit" disabled={busyDocumentId === document.id} onClick={() => setEditingDocumentId(document.id)}>
                          <Pencil size={17} />
                        </button>
                      )}
                      <button className="iconButton danger" type="button" aria-label={`Delete ${document.filename}`} title="Delete" disabled={busyDocumentId === document.id} onClick={() => void removeDocument(document)}>
                        <Trash2 size={17} />
                      </button>
                    </div>
                  </article>
                )) : (
                  <div className="emptyState">No source PDF indexed.</div>
                )}
              </div>
            )}

            {dialog === 'runtime' && (
              <div className="runtimeGrid">
                <div><strong>{status?.asrAvailable ? 'ASR ready' : 'ASR blocked'}</strong><span>{status?.asrDetail ?? 'Checking Riva ASR'}</span></div>
                <div><strong>Docling</strong><span>{status?.doclingBaseUrl ?? '-'}</span></div>
                <div><strong>{status?.qdrantAvailable ? 'Qdrant graph ready' : 'Embedding local'}</strong><span>{status?.retrievalProvider ?? status?.embeddingBaseUrl ?? '-'}</span></div>
                <div><strong>{status?.postgresAvailable ? 'Postgres ledger ready' : 'Postgres blocked'}</strong><span>Agent session, task, history, context and prompts.</span></div>
                <div><strong>{status?.llmAvailable ? 'LLM ready' : 'LLM fallback'}</strong><span>{status?.graphRagEnabled ? 'Graph RAG enabled' : 'Graph RAG disabled'}</span></div>
                <div><strong>Sources</strong><span>{status?.documentCount ?? 0} documents, {status?.chunkCount ?? 0} chunks</span></div>
              </div>
            )}

            {dialog === 'trace' && (
              <div className="traceCanvasStack">
                <AgentTraceCanvas turn={turn} status={status} events={activeSession?.events ?? turn?.agentEvents ?? []} />
                <div className="agentStatusStrip">
                  {(activeSession?.events ?? turn?.agentEvents ?? []).slice(-5).map((event) => (
                    <span key={event.id}>{event.agent}{event.target ? ` -> ${event.target}` : ''}: {event.status}</span>
                  ))}
                  {!(activeSession?.events ?? turn?.agentEvents ?? []).length && <span>No live agent events yet.</span>}
                </div>
                <div className="traceGrid compact">
                  {turn ? turn.agentTrace.map((trace) => (
                    <div key={trace.agent}>
                      <strong>{trace.agent}</strong>
                      <span>{trace.status}</span>
                      <p>{trace.message}</p>
                    </div>
                  )) : (
                    <div className="emptyState">No completed trace.</div>
                  )}
                </div>
              </div>
            )}

            {dialog === 'avatar' && (
              <div className="avatarDialog">
                <div className="avatarPickerGrid" aria-label="Face model">
                  {faceModels.map((model) => (
                    <button className={selectedModelId === model.id ? 'modelChoice active' : 'modelChoice'} key={model.id} type="button" onClick={() => handleModelChange(model.id)}>
                      <span>{model.label}</span>
                      <small>{Math.round(model.scale * 100)}% size / {Math.round(model.expression * 100)}% expression</small>
                      {selectedModelId === model.id ? <Check size={16} /> : null}
                    </button>
                  ))}
                </div>
                <div className="avatarTuning">
                  <label>
                    <span>Face size</span>
                    <input type="range" min="0.82" max="1.45" step="0.01" value={faceScale} onChange={(event) => setFaceScale(Number(event.target.value))} />
                    <strong>{Math.round(faceScale * 100)}%</strong>
                  </label>
                  <label>
                    <span>Expression</span>
                    <input type="range" min="0.2" max="1" step="0.01" value={expressionIntensity} onChange={(event) => setExpressionIntensity(Number(event.target.value))} />
                    <strong>{Math.round(expressionIntensity * 100)}%</strong>
                  </label>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </section>
  );
}

function dialogTitle(dialog: Exclude<DialogName, null>): string {
  if (dialog === 'sources') {
    return 'Knowledge';
  }
  if (dialog === 'runtime') {
    return 'Runtime';
  }
  if (dialog === 'avatar') {
    return 'Avatar';
  }
  return 'Trace';
}
