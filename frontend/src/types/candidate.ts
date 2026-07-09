import type { components } from './openapi';

export type ValidationNote = components['schemas']['ValidationNote'];
export type DescriptorSet = components['schemas']['DescriptorSet'];
export type TriageFlags = components['schemas']['TriageFlags'];
export type SimilarityNeighbor = components['schemas']['SimilarityNeighbor'];
export type ValidCandidate = components['schemas']['ValidCandidate'];
export type InvalidCandidate = components['schemas']['InvalidCandidate'];
export type Candidate = ValidCandidate | InvalidCandidate;
export type CandidateSet = components['schemas']['CandidateSet'];
export type ProjectionPoint = components['schemas']['ProjectionPoint'];
