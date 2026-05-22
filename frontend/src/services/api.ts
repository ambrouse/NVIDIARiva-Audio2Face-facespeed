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
