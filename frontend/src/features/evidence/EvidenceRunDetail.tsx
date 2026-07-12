import { useState } from 'react';

import type {
  ArtifactInventory,
  CandidateEvidence,
  EvidenceRunSummary,
  EvidenceValidation,
} from '../../types/evidence';
import { PredictionPanel } from './PredictionPanel';

type DetailTab = 'predictions' | 'validation' | 'artifacts' | 'provenance';

interface EvidenceRunDetailProps {
  run: EvidenceRunSummary;
  candidateEvidence: CandidateEvidence | null;
  artifacts: ArtifactInventory | null;
  validation: EvidenceValidation | null;
  onReport: (format: 'markdown' | 'html') => void;
  reportPending: boolean;
}

function countLabel(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export function EvidenceRunDetail({
  run,
  candidateEvidence,
  artifacts,
  validation,
  onReport,
  reportPending,
}: EvidenceRunDetailProps) {
  const [tab, setTab] = useState<DetailTab>('predictions');
  const failedChecks = run.validation_counts.fail_count;

  return (
    <section className="evidence-detail" aria-label={`${run.run_id} evidence review`}>
      <header className="evidence-detail-header">
        <div>
          <p className="eyebrow">Evidence run</p>
          <h2>{run.run_id}</h2>
          <p>{run.method.upstream_tool ?? run.method.adapter_id}</p>
        </div>
        <div className="detail-actions">
          <span className={`run-state ${run.state}`}>{run.state}</span>
          <button type="button" onClick={() => onReport('markdown')} disabled={reportPending}>
            Markdown report
          </button>
          <button type="button" onClick={() => onReport('html')} disabled={reportPending}>
            HTML report
          </button>
        </div>
      </header>

      {(run.state === 'failed' || run.state === 'partial') && (
        <div className="run-problem">
          <strong>{run.state === 'failed' ? 'Run failed' : 'Run completed partially'}</strong>
          <span>{run.failure?.message ?? `Missing outputs: ${run.missing_outputs.join(', ') || 'not recorded'}`}</span>
        </div>
      )}
      {failedChecks > 0 && (
        <div className="validation-alert">
          <strong>{countLabel(failedChecks, 'failed check')}</strong>
          <span>Validation failures remain evidence for expert review.</span>
        </div>
      )}

      <div className="evidence-tabs" role="tablist" aria-label="Evidence review sections">
        {(['predictions', 'validation', 'artifacts', 'provenance'] as const).map((name) => (
          <button
            type="button"
            role="tab"
            aria-selected={tab === name}
            className={tab === name ? 'active' : ''}
            key={name}
            onClick={() => setTab(name)}
          >
            {name[0].toUpperCase() + name.slice(1)}
          </button>
        ))}
      </div>

      <div className="evidence-tab-content">
        {tab === 'predictions' && <PredictionPanel evidence={candidateEvidence} />}
        {tab === 'validation' && (
          <section className="review-section">
            <h3>Artifact integrity</h3>
            {validation ? (
              <div className="metric-row">
                <span>{validation.counts.verified_count} verified</span>
                <span>{validation.counts.missing_count} missing</span>
                <span>{validation.counts.mismatch_count} mismatched</span>
                <span>{validation.counts.unsafe_path_count} unsafe paths</span>
              </div>
            ) : <p className="muted">Loading artifact validation…</p>}
            <h3>Scientific validation</h3>
            {candidateEvidence?.validation_results.length ? (
              <div className="validation-list">
                {candidateEvidence.validation_results.map((result) => (
                  <article className={`validation-result ${result.status}`} key={result.id}>
                    <strong>{result.check_id}</strong>
                    <span className="validation-status">{result.status}</span>
                    <p>{result.explanation}</p>
                    <small>{result.validator} {result.validator_version}</small>
                  </article>
                ))}
              </div>
            ) : <p className="muted">No ligand-bound validation results were recorded.</p>}
          </section>
        )}
        {tab === 'artifacts' && (
          <section className="review-section">
            <h3>Artifact inventory</h3>
            {artifacts?.artifacts.length ? (
              <div className="artifact-list">
                {artifacts.artifacts.map((artifact) => (
                  <article className="artifact-item" key={artifact.artifact_id}>
                    <div>
                      <strong>{artifact.semantic?.logical_name ?? artifact.original_name}</strong>
                      <p>{artifact.semantic?.artifact_type ?? artifact.role} · {artifact.media_type}</p>
                    </div>
                    <span className={`verification ${artifact.verification.status}`}>
                      {artifact.verification.status}
                    </span>
                    <code>{artifact.content_digest}</code>
                  </article>
                ))}
              </div>
            ) : <p className="muted">No artifacts are available for this run.</p>}
          </section>
        )}
        {tab === 'provenance' && (
          <section className="review-section provenance-grid">
            <div><span>Method ID</span><strong>{run.method.method_id}</strong></div>
            <div><span>Adapter</span><strong>{run.method.adapter_id} {run.method.adapter_version}</strong></div>
            <div><span>Upstream tool</span><strong>{run.method.upstream_tool ?? 'Not recorded'}</strong></div>
            <div><span>Version</span><strong>{run.method.upstream_version ?? 'Not recorded'}</strong></div>
            <div><span>Seed(s)</span><strong>{run.method.random_seeds.join(', ') || 'Not recorded'}</strong></div>
            <div><span>Completed</span><strong>{run.finished_at ?? 'Not recorded'}</strong></div>
            <div className="wide"><span>Command</span><code>{run.method.command.join(' ') || 'Not recorded'}</code></div>
          </section>
        )}
      </div>
    </section>
  );
}
