import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { CandidateDetail } from './CandidateDetail';
import type { Candidate } from '../types/candidate';
import { fetchCandidateConformer } from '../api/candidates';

vi.mock('../api/candidates', () => ({
  fetchCandidateConformer: vi.fn(),
}));

const candidate: Candidate = {
  id: 'demo-1',
  name: 'Aspirin',
  smiles: 'CC(=O)Oc1ccccc1C(=O)O',
  canonical_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
  source: 'manual_demo',
  external_id: 'DEMO-001',
  score: -7.1,
  target: 'demo-target',
  notes: null,
  is_valid: true,
  validation_notes: [],
  descriptors: {
    molecular_weight: 180.2,
    logp: 1.2,
    tpsa: 63.6,
    hbond_donors: 1,
    hbond_acceptors: 3,
    rotatable_bonds: 2,
    ring_count: 1,
    heavy_atom_count: 13,
    fraction_csp3: 0.1,
    murcko_scaffold: 'c1ccccc1',
  },
  triage_flags: {
    lipinski_violations: 0,
    lipinski_notes: [],
    veber_violations: 0,
    veber_notes: [],
  },
  structure_svg: '<svg><title>Aspirin</title></svg>',
  neighbors: [{ candidate_id: 'demo-2', name: 'Acetaminophen', similarity: 0.31 }],
};

describe('CandidateDetail', () => {
  it('renders structure, descriptors, triage, and neighbors', () => {
    render(<CandidateDetail candidate={candidate} />);

    expect(screen.getByRole('heading', { name: 'Aspirin' })).toBeInTheDocument();
    expect(screen.getByLabelText('2D structure of Aspirin')).toBeInTheDocument();
    expect(screen.getByText('2D depiction. Not a binding pose.')).toBeInTheDocument();
    expect(screen.getByText('Mol weight')).toBeInTheDocument();
    expect(screen.getByText('No rule flags')).toBeInTheDocument();
    expect(screen.getByText('Acetaminophen')).toBeInTheDocument();
  });

  it('shows a stable loading state while the 3D conformer is loading', async () => {
    vi.mocked(fetchCandidateConformer).mockReturnValue(new Promise(() => {}));

    render(<CandidateDetail candidate={candidate} />);

    await userEvent.click(screen.getByRole('button', { name: '3D conformer' }));

    expect(screen.getByText('Loading 3D conformer...')).toBeInTheDocument();
    expect(
      screen.queryByText('Select a valid molecule to view a 3D conformer.'),
    ).not.toBeInTheDocument();
  });
});
