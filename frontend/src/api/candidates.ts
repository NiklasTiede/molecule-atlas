import type { CandidateSet, ProjectionPoint } from '../types/candidate';
import type { paths } from '../types/openapi';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export function fetchDemoCandidateSet(): Promise<CandidateSet> {
  return fetchJson<CandidateSet>('/api/candidate-sets/demo');
}

export function fetchDemoProjection(): Promise<ProjectionPoint[]> {
  return fetchJson<ProjectionPoint[]>('/api/candidate-sets/demo/projection');
}

export type CandidateConformer = paths['/api/candidate-sets/demo/candidates/{candidate_id}/conformer']['get']['responses'][200]['content']['application/json'];

export function fetchCandidateConformer(candidateId: string): Promise<CandidateConformer> {
  return fetchJson<CandidateConformer>(
    `/api/candidate-sets/demo/candidates/${candidateId}/conformer`,
  );
}
