import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { CandidateTable } from './CandidateTable';
import type { Candidate } from '../types/candidate';

const candidates: Candidate[] = [
  {
    id: 'demo-1',
    name: 'Aspirin',
    smiles: 'CC(=O)Oc1ccccc1C(=O)O',
    canonical_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
    source: 'manual_demo',
    external_id: 'DEMO-001',
    score: -7.1,
    target: 'demo-target',
    notes: null,
    status: 'valid',
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
    structure_svg: '<svg></svg>',
    neighbors: [],
  },
  {
    id: 'demo-2',
    name: 'Invalid Demo',
    smiles: 'not_a_smiles',
    canonical_smiles: null,
    source: 'manual_demo',
    external_id: 'DEMO-BAD',
    score: null,
    target: 'demo-target',
    notes: null,
    status: 'invalid',
    is_valid: false,
    validation_notes: [{ level: 'error', message: 'Invalid SMILES: not_a_smiles' }],
    descriptors: null,
    triage_flags: null,
    structure_svg: null,
    neighbors: [],
  },
];

describe('CandidateTable', () => {
  it('filters invalid rows when valid-only is checked', async () => {
    const user = userEvent.setup();

    render(<CandidateTable candidates={candidates} selectedId="demo-1" onSelect={vi.fn()} />);

    expect(screen.getByText('Invalid Demo')).toBeInTheDocument();

    await user.click(screen.getByLabelText('Valid only'));

    expect(screen.queryByText('Invalid Demo')).not.toBeInTheDocument();
    expect(screen.getByText('Aspirin')).toBeInTheDocument();
  });

  it('notifies when a candidate row is selected', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(<CandidateTable candidates={candidates} selectedId="demo-1" onSelect={onSelect} />);

    await user.click(screen.getByText('Invalid Demo'));

    expect(onSelect).toHaveBeenCalledWith('demo-2');
  });
});
