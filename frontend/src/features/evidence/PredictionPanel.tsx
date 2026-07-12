import type { CandidateEvidence, Prediction } from '../../types/evidence';

const labels: Record<Prediction['type'], string> = {
  docking_energy: 'Docking energy',
  pose_confidence: 'Pose confidence',
  structure_confidence: 'Structure confidence',
  binder_probability: 'Binder probability',
  predicted_affinity: 'Predicted affinity',
};

const directionLabels = {
  lower_is_better: 'Lower is better within this method only',
  higher_is_better: 'Higher is better within this method only',
} as const;

function PredictionCard({ prediction }: { prediction: Prediction }) {
  return (
    <article className="prediction-card">
      <div className="prediction-heading">
        <div>
          <p className="eyebrow">{prediction.scope} · {prediction.scope_id}</p>
          <h3>{labels[prediction.type]}</h3>
        </div>
        <strong className="prediction-value">
          {prediction.value} {prediction.unit ?? ''}
        </strong>
      </div>
      <p className="direction-note">{directionLabels[prediction.optimization_direction]}</p>
      <p>{prediction.interpretation}</p>
      <dl className="compact-definitions">
        <dt>Method</dt><dd>{prediction.method_id}</dd>
        <dt>Raw source</dt>
        <dd>{prediction.raw_source.artifact_id} · {prediction.raw_source.field}</dd>
      </dl>
      {prediction.caveats.length > 0 && (
        <ul className="caveat-list">
          {prediction.caveats.map((caveat) => <li key={caveat}>{caveat}</li>)}
        </ul>
      )}
    </article>
  );
}

export function PredictionPanel({ evidence }: { evidence: CandidateEvidence | null }) {
  if (!evidence) {
    return <div className="empty-evidence">No ligand input is recorded for candidate binding.</div>;
  }
  return (
    <section aria-label="Typed predictions">
      <div className={`binding-banner ${evidence.binding.status}`}>
        <strong>Candidate binding: {evidence.binding.status}</strong>
        <span>{evidence.binding.explanation}</span>
      </div>
      {evidence.warnings.map((warning) => (
        <p className="warning-banner" key={warning.code}>{warning.message}</p>
      ))}
      {evidence.predictions.length === 0 ? (
        <div className="empty-evidence">No typed predictions are bound to this ligand input.</div>
      ) : (
        <div className="prediction-grid">
          {evidence.predictions.map((prediction) => (
            <PredictionCard prediction={prediction} key={prediction.id} />
          ))}
        </div>
      )}
      <p className="scientific-notice">
        Computational predictions are evidence for expert review, not experimental conclusions.
      </p>
    </section>
  );
}
