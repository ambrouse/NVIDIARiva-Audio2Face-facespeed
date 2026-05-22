const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export type ServiceStatus = {
  name: string;
  state: string;
  healthy: boolean;
  detail: string;
  managerMode: string;
  containerName: string | null;
  containerState: string | null;
  containerStatus: string | null;
  containerImage: string | null;
};

export type Job = {
  id: string;
  state: string;
  text: string;
  voice: string;
  language: string;
  a2fProfile: string;
  outputMode: string;
  audioPath: string | null;
  resultPath: string | null;
  audioUrl: string | null;
  animationUrl: string | null;
  error: string | null;
};

export type SystemCheck = {
  name: string;
  ok: boolean;
  detail: string;
};

export type AnimationFrame = {
  t: number;
  jawOpen: number;
  mouthWide: number;
  mouthSmile: number;
  blendShapes?: Record<string, number>;
};

export type AnimationTimeline = {
  engine: string;
  frames: AnimationFrame[];
  model?: string;
  modelAsset?: string;
};

export type RagRuntimeStatus = {
  asrAvailable: boolean;
  asrDetail: string;
  documentCount: number;
  chunkCount: number;
  languages: string[];
  doclingBaseUrl: string;
  embeddingBaseUrl: string;
  parseProvider: string;
  retrievalProvider: string;
};

export type RagDocument = {
  id: string;
  filename: string;
  title: string;
  language: string;
  status: string;
  checksum: string;
  pageCount: number;
  chunkCount: number;
  summary: string;
};

export type Citation = {
  chunkId: string;
  documentId: string;
  source: string;
  page: number;
  titlePath: string[];
  excerpt: string;
  confidence: number;
};

export type AgentTrace = {
  agent: string;
  status: string;
  message: string;
  evidenceChunkIds: string[];
};

export type VoiceTurn = {
  id: string;
  language: string;
  transcript: {
    text: string;
    language: string;
    confidence: number;
    source: string;
  };
  answer: {
    text: string;
    citations: Citation[];
    reviewStatus: string;
  };
  audioUrl: string | null;
  animationUrl: string | null;
  jobId: string | null;
  agentTrace: AgentTrace[];
};

export type Transcript = VoiceTurn['transcript'];

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(resolveApiUrl(path), {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'network error';
    throw new Error(`Cannot reach backend API at ${resolveApiUrl(path)}. Check that the backend is running on port 8020. ${detail}`);
  }

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function fetchServices(): Promise<ServiceStatus[]> {
  return request<ServiceStatus[]>('/api/services');
}

export function runServiceAction(serviceName: string, action: 'start' | 'stop' | 'restart'): Promise<ServiceStatus> {
  return request<ServiceStatus>(`/api/services/${serviceName}/${action}`, { method: 'POST' });
}

export function fetchServiceLogs(serviceName: string): Promise<string[]> {
  return request<string[]>(`/api/services/${serviceName}/logs`);
}

export type CreateJobInput = {
  text: string;
  voice: string;
  language: string;
  a2fProfile: string;
  outputMode: string;
};

export function resolveApiUrl(path: string): string {
  if (path.startsWith('http')) {
    return path;
  }
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function fetchAnimationTimeline(urlOrPath: string): Promise<AnimationTimeline> {
  const response = await fetch(resolveApiUrl(urlOrPath));
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<AnimationTimeline>;
}

export function createJob(input: CreateJobInput): Promise<Job> {
  return request<Job>('/api/jobs', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function fetchSystemChecks(): Promise<SystemCheck[]> {
  return request<SystemCheck[]>('/api/system/checks');
}

export function fetchRagStatus(): Promise<RagRuntimeStatus> {
  return request<RagRuntimeStatus>('/api/rag/status');
}

export function fetchDocuments(): Promise<RagDocument[]> {
  return request<RagDocument[]>('/api/documents');
}

export async function uploadDocument(file: File, language: string): Promise<RagDocument> {
  const response = await fetch(resolveApiUrl(`/api/documents?filename=${encodeURIComponent(file.name)}&language=${encodeURIComponent(language)}`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/pdf' },
    body: await file.arrayBuffer(),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Upload failed with status ${response.status}`);
  }
  return response.json() as Promise<RagDocument>;
}

export function createVoiceTurn(input: { message: string; language: string; voice: string; outputMode: string }): Promise<VoiceTurn> {
  return request<VoiceTurn>('/api/voice/chat', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function transcribeVoice(audio: Blob): Promise<Transcript> {
  const response = await fetch(resolveApiUrl('/api/voice/transcribe'), {
    method: 'POST',
    headers: { 'Content-Type': audio.type || 'audio/webm' },
    body: audio,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Transcription failed with status ${response.status}`);
  }
  return response.json() as Promise<Transcript>;
}
