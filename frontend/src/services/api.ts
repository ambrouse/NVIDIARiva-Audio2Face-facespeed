const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8020';

export type ServiceStatus = {
  name: string;
  state: string;
  healthy: boolean;
  detail: string;
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
  error: string | null;
};

export type SystemCheck = {
  name: string;
  ok: boolean;
  detail: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

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

export function createJob(input: CreateJobInput): Promise<Job> {
  return request<Job>('/api/jobs', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function fetchSystemChecks(): Promise<SystemCheck[]> {
  return request<SystemCheck[]>('/api/system/checks');
}
