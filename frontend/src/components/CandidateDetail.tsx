import { useEffect, useRef, useState } from 'react';

import { fetchCandidateConformer } from '../api/candidates';
import type { Candidate, DescriptorSet } from '../types/candidate';
import { Molecule2D } from './Molecule2D';
import { Molecule3D } from './Molecule3D';
import { TriageFlags } from './TriageFlags';

type CandidateDetailProps = {
  candidate: Candidate | null;
};

const descriptorLabels: Array<[keyof DescriptorSet, string]> = [
  ['molecular_weight', 'Mol weight'],
  ['logp', 'LogP'],
  ['tpsa', 'TPSA'],
  ['hbond_donors', 'HBD'],
  ['hbond_acceptors', 'HBA'],
  ['rotatable_bonds', 'Rot bonds'],
  ['ring_count', 'Rings'],
  ['heavy_atom_count', 'Heavy atoms'],
  ['fraction_csp3', 'Frac. sp3'],
];

function formatDescriptor(value: number | string | null): string {
  if (value === null) {
    return '-';
  }
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return value;
}

export function CandidateDetail({ candidate }: CandidateDetailProps) {
  const [activeView, setActiveView] = useState<'2d' | '3d'>('2d');
  const [conformer, setConformer] = useState<{ candidateId: string; molBlock: string } | null>(
    null,
  );
  const [conformerError, setConformerError] = useState<{
    candidateId: string;
    message: string;
  } | null>(null);
  const [loadingConformerId, setLoadingConformerId] = useState<string | null>(null);
  const pendingConformerId = useRef<string | null>(null);

  useEffect(() => {
    if (!candidate?.is_valid || activeView !== '3d') {
      return;
    }
    if (conformer?.candidateId === candidate.id || conformerError?.candidateId === candidate.id) {
      return;
    }
    if (pendingConformerId.current === candidate.id) {
      return;
    }

    pendingConformerId.current = candidate.id;
    setLoadingConformerId(candidate.id);
    fetchCandidateConformer(candidate.id)
      .then((loadedConformer) =>
        setConformer({ candidateId: loadedConformer.candidate_id, molBlock: loadedConformer.mol_block }),
      )
      .catch((caught: unknown) => {
        setConformerError(
          {
            candidateId: candidate.id,
            message: caught instanceof Error ? caught.message : 'Could not load the 3D conformer.',
          },
        );
      })
      .finally(() => {
        if (pendingConformerId.current === candidate.id) {
          pendingConformerId.current = null;
          setLoadingConformerId(null);
        }
      });
  }, [activeView, candidate, conformer, conformerError]);

  if (!candidate) {
    return (
      <aside className="detail-panel empty-panel">
        <p>Select a candidate to inspect its structure and properties.</p>
      </aside>
    );
  }

  return (
    <aside className="detail-panel" aria-label={`${candidate.name} detail`}>
      <div className="detail-header">
        <div>
          <h2>{candidate.name}</h2>
          <div className="smiles">{candidate.canonical_smiles ?? candidate.smiles}</div>
        </div>
        <span className={candidate.is_valid ? 'state-chip valid' : 'state-chip invalid'}>
          {candidate.is_valid ? 'Valid' : 'Invalid'}
        </span>
      </div>

      <div className="detail-tabs" aria-label="Structure view options">
        <button
          className={activeView === '2d' ? 'active' : undefined}
          type="button"
          onClick={() => setActiveView('2d')}
        >
          2D
        </button>
        <button
          className={activeView === '3d' ? 'active' : undefined}
          type="button"
          disabled={!candidate.is_valid}
          onClick={() => setActiveView('3d')}
        >
          3D conformer
        </button>
      </div>

      <div className="structure-frame">
        {activeView === '2d' ? <Molecule2D svg={candidate.structure_svg} name={candidate.name} /> : null}
        {activeView === '3d' && conformerError?.candidateId === candidate.id ? (
          <div className="empty-structure">{conformerError.message}</div>
        ) : null}
        {activeView === '3d' &&
        conformerError?.candidateId !== candidate.id &&
        loadingConformerId === candidate.id ? (
          <div className="empty-structure">Loading 3D conformer...</div>
        ) : null}
        {activeView === '3d' &&
        conformerError?.candidateId !== candidate.id &&
        loadingConformerId !== candidate.id ? (
          <Molecule3D molBlock={conformer?.candidateId === candidate.id ? conformer.molBlock : null} />
        ) : null}
        <span className="structure-caveat">
          {activeView === '2d'
            ? '2D depiction. Not a binding pose.'
            : 'Generated conformer. Not a docked binding pose.'}
        </span>
      </div>

      <section className="detail-section">
        <h3>Descriptors</h3>
        {candidate.descriptors ? (
          <div className="descriptor-grid">
            {descriptorLabels.map(([key, label]) => (
              <div className="metric" key={key}>
                <label>{label}</label>
                <strong>{formatDescriptor(candidate.descriptors?.[key] ?? null)}</strong>
              </div>
            ))}
            <div className="metric wide">
              <label>Murcko scaffold</label>
              <strong>{candidate.descriptors.murcko_scaffold ?? '-'}</strong>
            </div>
          </div>
        ) : (
          <p className="muted">Descriptors are unavailable for invalid molecules.</p>
        )}
      </section>

      <section className="detail-section">
        <h3>Triage Flags</h3>
        <TriageFlags flags={candidate.triage_flags} />
      </section>

      <section className="detail-section">
        <h3>Nearest Neighbors</h3>
        {candidate.neighbors.length > 0 ? (
          <div className="neighbor-list">
            {candidate.neighbors.slice(0, 5).map((neighbor) => (
              <div className="neighbor-row" key={neighbor.candidate_id}>
                <span>{neighbor.name}</span>
                <strong>{neighbor.similarity.toFixed(2)}</strong>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No neighbors available for this candidate.</p>
        )}
      </section>

      {candidate.validation_notes.length > 0 ? (
        <section className="detail-section">
          <h3>Validation Notes</h3>
          <ul className="notes-list">
            {candidate.validation_notes.map((note) => (
              <li key={`${note.level}-${note.message}`}>{note.message}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </aside>
  );
}
