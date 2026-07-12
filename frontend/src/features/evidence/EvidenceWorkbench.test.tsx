import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as evidenceApi from '../../api/evidence';
import type {
  ArtifactInventory,
  CandidateEvidence,
  EvidenceRunList,
  EvidenceRunSummary,
  EvidenceValidation,
  EvidenceImport,
} from '../../types/evidence';
import { EvidenceWorkbench } from './EvidenceWorkbench';

vi.mock('../../api/evidence');

const run: EvidenceRunSummary = {
  run_id: 'fixture-succeeded',
  schema_version: '0.1.0',
  state: 'succeeded',
  started_at: '2026-01-01T00:00:00Z',
  finished_at: '2026-01-01T00:00:01Z',
  expected_outputs: ['predicted pose'],
  missing_outputs: [],
  failure: null,
  method: {
    method_id: 'synthetic-method',
    adapter_id: 'manifest',
    adapter_version: '0.1.0',
    upstream_tool: 'Synthetic Evidence Fixture',
    upstream_version: '1.0.0',
    source_commit: null,
    checkpoint_id: null,
    checkpoint_sha256: null,
    container_image: null,
    container_digest: null,
    command: ['synthetic-fixture', 'predict'],
    random_seeds: [61453],
  },
  ligand_inputs: [
    {
      input_id: 'ligand-input',
      artifact_id: 'ligand',
      representation: 'conformer',
      upstream_id: 'synthetic-ligand-1',
    },
  ],
  artifact_count: 4,
  prediction_count: 2,
  validation_counts: {
    pass_count: 1,
    fail_count: 1,
    warning_count: 0,
    unavailable_count: 0,
    error_count: 0,
  },
  warnings: [],
};

const runList: EvidenceRunList = {
  contract_version: '0.1.0',
  capability_id: 'list_evidence_runs',
  capability_version: '0.1.0',
  correlation_id: 'corr-list',
  total: 1,
  offset: 0,
  limit: 20,
  runs: [run],
};

const candidateEvidence: CandidateEvidence = {
  contract_version: '0.1.0',
  capability_id: 'get_candidate_evidence',
  capability_version: '0.1.0',
  correlation_id: 'corr-evidence',
  run_id: run.run_id,
  binding: {
    status: 'bound',
    candidate_id: 'synthetic-ligand-1',
    candidate_external_id: null,
    reference_ids_checked: ['synthetic-ligand-1'],
    matched_input_ids: ['ligand-input'],
    matched_input_artifact_ids: ['ligand'],
    explanation: 'One recorded ligand input matches the candidate references exactly.',
  },
  method: run.method,
  lineage_available: true,
  related_artifact_ids: ['ligand', 'raw-predictions'],
  prediction_total: 2,
  prediction_limit: 50,
  predictions: [
    {
      id: 'energy-1',
      type: 'docking_energy',
      value: -7.4,
      unit: 'kcal/mol',
      optimization_direction: 'lower_is_better',
      scope: 'pose',
      scope_id: 'pose-1',
      method_id: 'synthetic-method',
      raw_source: {
        artifact_id: 'raw-predictions',
        field: 'docking_energy',
        upstream_record_id: 'pose-1',
      },
      uncertainty: null,
      interpretation: 'Synthetic docking energy; not measured binding affinity.',
      caveats: ['The fixture does not model a real receptor or ligand.'],
    },
  ],
  validation_total: 1,
  validation_limit: 100,
  validation_results: [],
  warnings: [],
};

const artifacts: ArtifactInventory = {
  contract_version: '0.1.0',
  capability_id: 'list_available_artifacts',
  capability_version: '0.1.0',
  correlation_id: 'corr-artifacts',
  run_id: run.run_id,
  total: 0,
  offset: 0,
  limit: 50,
  artifacts: [],
};

const validation: EvidenceValidation = {
  contract_version: '0.1.0',
  capability_id: 'validate_evidence_artifacts',
  capability_version: '0.1.0',
  correlation_id: 'corr-validation',
  run_id: run.run_id,
  counts: {
    verified_count: 4,
    missing_count: 0,
    mismatch_count: 0,
    external_count: 0,
    unsafe_path_count: 0,
    unreadable_count: 0,
  },
  artifact_checks: [],
  warnings: [],
};

const importedRun: EvidenceImport = {
  contract_version: '0.1.0',
  capability_id: 'import_evidence_bundle',
  capability_version: '0.1.0',
  correlation_id: 'corr-import',
  idempotency_replayed: false,
  run: { ...run, run_id: 'fixture-imported' },
};

describe('EvidenceWorkbench', () => {
  beforeEach(() => {
    vi.mocked(evidenceApi.fetchEvidenceRuns).mockResolvedValue(runList);
    vi.mocked(evidenceApi.fetchEvidenceRun).mockResolvedValue(run);
    vi.mocked(evidenceApi.fetchCandidateEvidence).mockResolvedValue(candidateEvidence);
    vi.mocked(evidenceApi.fetchEvidenceArtifacts).mockResolvedValue(artifacts);
    vi.mocked(evidenceApi.fetchEvidenceValidation).mockResolvedValue(validation);
    vi.mocked(evidenceApi.importEvidenceBundle).mockResolvedValue(importedRun);
  });

  it('shows typed prediction semantics and keeps validation failures prominent', async () => {
    const user = userEvent.setup();
    render(<EvidenceWorkbench />);

    expect(screen.getByText('Loading evidence runs…')).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: 'Docking energy' })).toBeInTheDocument();
    expect(screen.getByText('-7.4 kcal/mol')).toBeInTheDocument();
    expect(screen.getByText('Lower is better within this method only')).toBeInTheDocument();
    expect(screen.getByText('not measured binding affinity.', { exact: false })).toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: 'Validation' }));
    expect(screen.getByText('1 failed check')).toBeInTheDocument();
    expect(screen.getByText('Validation failures remain evidence for expert review.')).toBeInTheDocument();
  });

  it('surfaces an empty run index without inventing evidence', async () => {
    vi.mocked(evidenceApi.fetchEvidenceRuns).mockResolvedValue({ ...runList, total: 0, runs: [] });

    render(<EvidenceWorkbench />);

    expect(await screen.findByText('No evidence runs are available yet.')).toBeInTheDocument();
    expect(screen.getByText('Import a portable evidence bundle to begin review.')).toBeInTheDocument();
  });

  it('imports through the typed command and refreshes the run index', async () => {
    const user = userEvent.setup();
    render(<EvidenceWorkbench />);

    await screen.findByRole('heading', { name: 'Docking energy' });
    const upload = screen.getByLabelText('Import evidence bundle');
    await user.upload(upload, new File(['synthetic bundle'], 'evidence.zip', { type: 'application/zip' }));

    expect(await screen.findByText('Imported evidence run fixture-imported.')).toBeInTheDocument();
    expect(evidenceApi.importEvidenceBundle).toHaveBeenCalledWith(
      expect.any(File),
      expect.any(String),
    );
  });
});
