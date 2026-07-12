import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import { fetchDemoCandidateSet, fetchDemoProjection } from './api/candidates';
import { CandidateDetail } from './components/CandidateDetail';
import { CandidateTable } from './components/CandidateTable';
import { EvidenceWorkbench } from './features/evidence/EvidenceWorkbench';
import type { Candidate, CandidateSet, ProjectionPoint } from './types/candidate';

const ChemicalSpacePlot = lazy(() =>
  import('./components/ChemicalSpacePlot').then((module) => ({
    default: module.ChemicalSpacePlot,
  })),
);

export function App() {
  const [activeView, setActiveView] = useState<'candidates' | 'evidence'>('candidates');
  const [candidateSet, setCandidateSet] = useState<CandidateSet | null>(null);
  const [projection, setProjection] = useState<ProjectionPoint[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchDemoCandidateSet(), fetchDemoProjection()])
      .then(([candidateData, projectionData]) => {
        setCandidateSet(candidateData);
        setProjection(projectionData);
        setSelectedId(candidateData.candidates[0]?.id ?? null);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : 'Could not load candidate set.');
      });
  }, []);

  const selectedCandidate = useMemo<Candidate | null>(() => {
    return candidateSet?.candidates.find((candidate) => candidate.id === selectedId) ?? null;
  }, [candidateSet, selectedId]);

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <h1>Molecule Atlas</h1>
          <p>Scientific evidence workbench</p>
        </div>
        <nav className="primary-nav" aria-label="Main workspace">
          <button
            type="button"
            className={activeView === 'candidates' ? 'active' : ''}
            onClick={() => setActiveView('candidates')}
          >
            Candidates
          </button>
          <button
            type="button"
            className={activeView === 'evidence' ? 'active' : ''}
            onClick={() => setActiveView('evidence')}
          >
            Evidence Runs
          </button>
        </nav>
      </header>
      {activeView === 'evidence' ? <EvidenceWorkbench /> : (
        error ? (
          <section className="state-screen"><p>{error}</p></section>
        ) : !candidateSet ? (
          <section className="state-screen"><p>Loading candidate set...</p></section>
        ) : (
          <>
            <div className="candidate-context">
              <p>{candidateSet.name}</p>
              <div className="summary-strip" aria-label="Candidate set summary">
                <span>{candidateSet.candidates.length} candidates</span>
                <span>{candidateSet.candidates.filter((candidate) => candidate.is_valid).length} valid</span>
                <span>{candidateSet.candidates.filter((candidate) => !candidate.is_valid).length} invalid</span>
              </div>
            </div>
            <section className="workbench">
              <div className="left-workbench">
                <CandidateTable
                  candidates={candidateSet.candidates}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                />
                <Suspense fallback={<div className="plot-panel muted">Loading chemical-space plot...</div>}>
                  <ChemicalSpacePlot
                    points={projection}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                  />
                </Suspense>
              </div>
              <CandidateDetail candidate={selectedCandidate} />
            </section>
          </>
        )
      )}
    </main>
  );
}
