export type ValidationNote = {
  level: 'info' | 'warning' | 'error';
  message: string;
};

export type DescriptorSet = {
  molecular_weight: number;
  logp: number;
  tpsa: number;
  hbond_donors: number;
  hbond_acceptors: number;
  rotatable_bonds: number;
  ring_count: number;
  heavy_atom_count: number;
  fraction_csp3: number;
  murcko_scaffold: string | null;
};

export type TriageFlags = {
  lipinski_violations: number;
  lipinski_notes: string[];
  veber_violations: number;
  veber_notes: string[];
};

export type SimilarityNeighbor = {
  candidate_id: string;
  name: string;
  similarity: number;
};

export type Candidate = {
  id: string;
  name: string;
  smiles: string;
  canonical_smiles: string | null;
  source: string | null;
  external_id: string | null;
  score: number | null;
  target: string | null;
  notes: string | null;
  is_valid: boolean;
  validation_notes: ValidationNote[];
  descriptors: DescriptorSet | null;
  triage_flags: TriageFlags | null;
  structure_svg: string | null;
  neighbors: SimilarityNeighbor[];
};

export type CandidateSet = {
  id: string;
  name: string;
  candidates: Candidate[];
};

export type ProjectionPoint = {
  candidate_id: string;
  name: string;
  x: number;
  y: number;
};
