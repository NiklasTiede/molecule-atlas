import type { EvidenceComparison } from '../../types/evidence';

export function EvidenceComparison({ comparison }: { comparison: EvidenceComparison | null }) {
  if (!comparison) {
    return null;
  }
  return (
    <section className="comparison-panel" aria-label="Comparison result">
      <h2>Like-for-like comparison</h2>
      <p>
        Values appear together only when prediction type, unit, and optimization direction match.
        This view does not create a combined ranking.
      </p>
      {comparison.warnings.map((warning) => (
        <p className="warning-banner" key={`${warning.code}-${warning.subject_id ?? ''}`}>
          {warning.message}
        </p>
      ))}
      {comparison.prediction_groups.map((group) => (
        <article className="comparison-group" key={`${group.prediction_type}-${group.unit}`}>
          <h3>{group.prediction_type.replaceAll('_', ' ')}</h3>
          <p>{group.unit ?? 'unitless'} · {group.optimization_direction.replaceAll('_', ' ')}</p>
          <div className="comparison-values">
            {group.entries.map((entry) => (
              <div key={`${entry.subject_id}-${entry.prediction.id}`}>
                <span>{comparison.subjects.find((subject) => subject.subject_id === entry.subject_id)?.label}</span>
                <strong>{entry.prediction.value} {entry.prediction.unit ?? ''}</strong>
              </div>
            ))}
          </div>
        </article>
      ))}
    </section>
  );
}
