import type {
  ArtifactInventory,
  CandidateEvidence,
  ComparisonRequest,
  EvidenceComparison,
  EvidenceImport,
  EvidenceReport,
  EvidenceReportFormat,
  EvidenceRunList,
  EvidenceRunSummary,
  EvidenceValidation,
} from '../types/evidence';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function responseError(response: Response): Promise<Error> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return new Error(body?.detail ?? `API request failed: ${response.status} ${response.statusText}`);
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw await responseError(response);
  }
  return (await response.json()) as T;
}

export function fetchEvidenceRuns(): Promise<EvidenceRunList> {
  return fetchJson<EvidenceRunList>('/api/evidence/runs');
}

export async function fetchEvidenceRun(runId: string): Promise<EvidenceRunSummary> {
  const response = await fetchJson<{ run: EvidenceRunSummary }>(
    `/api/evidence/runs/${encodeURIComponent(runId)}`,
  );
  return response.run;
}

export function fetchEvidenceArtifacts(runId: string): Promise<ArtifactInventory> {
  return fetchJson<ArtifactInventory>(
    `/api/evidence/runs/${encodeURIComponent(runId)}/artifacts`,
  );
}

export function fetchEvidenceValidation(runId: string): Promise<EvidenceValidation> {
  return fetchJson<EvidenceValidation>(
    `/api/evidence/runs/${encodeURIComponent(runId)}/artifact-validation`,
  );
}

export function fetchCandidateEvidence(
  runId: string,
  candidateId: string,
): Promise<CandidateEvidence> {
  return fetchJson<CandidateEvidence>(
    `/api/evidence/runs/${encodeURIComponent(runId)}/candidates/${encodeURIComponent(candidateId)}/evidence`,
  );
}

export function compareCandidateEvidence(request: ComparisonRequest): Promise<EvidenceComparison> {
  return fetchJson<EvidenceComparison>('/api/evidence/comparisons', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
}

export function fetchEvidenceReport(
  runId: string,
  reportFormat: EvidenceReportFormat,
): Promise<EvidenceReport> {
  return fetchJson<EvidenceReport>(
    `/api/evidence/runs/${encodeURIComponent(runId)}/report?report_format=${reportFormat}`,
  );
}

export function importEvidenceBundle(file: File, idempotencyKey: string): Promise<EvidenceImport> {
  const body = new FormData();
  body.append('bundle', file);
  return fetchJson<EvidenceImport>('/api/evidence/imports', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body,
  });
}
