import type { components } from './openapi';

export type EvidenceRunSummary = components['schemas']['RunSummary'];
export type EvidenceRunList = components['schemas']['ListEvidenceRunsOutput'];
export type CandidateEvidence = components['schemas']['GetCandidateEvidenceOutput'];
export type ArtifactInventory = components['schemas']['ListAvailableArtifactsOutput'];
export type EvidenceValidation = components['schemas']['ValidateEvidenceArtifactsOutput'];
export type EvidenceComparison = components['schemas']['CompareCandidatesOutput'];
export type ComparisonRequest = components['schemas']['CompareCandidatesInput'];
export type EvidenceReport = components['schemas']['GenerateEvidenceReportOutput'];
export type EvidenceReportFormat = EvidenceReport['report_format'];
export type EvidenceImport = components['schemas']['ImportEvidenceBundleOutput'];
export type Prediction = CandidateEvidence['predictions'][number];
export type AvailableArtifact = ArtifactInventory['artifacts'][number];
