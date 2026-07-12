import type { EvidenceRunSummary } from '../../types/evidence';

interface EvidenceRunListProps {
  runs: EvidenceRunSummary[];
  selectedRunId: string | null;
  comparisonRunIds: string[];
  onSelect: (runId: string) => void;
  onToggleComparison: (runId: string) => void;
}

export function EvidenceRunList({
  runs,
  selectedRunId,
  comparisonRunIds,
  onSelect,
  onToggleComparison,
}: EvidenceRunListProps) {
  return (
    <div className="run-list" aria-label="Evidence run index">
      {runs.map((run) => (
        <article className={`run-card ${selectedRunId === run.run_id ? 'selected' : ''}`} key={run.run_id}>
          <button type="button" className="run-select" onClick={() => onSelect(run.run_id)}>
            <span className={`run-state ${run.state}`}>{run.state}</span>
            <strong>{run.run_id}</strong>
            <span>{run.method.upstream_tool ?? run.method.adapter_id}</span>
            <small>{run.prediction_count} predictions · {run.validation_counts.fail_count} failed checks</small>
          </button>
          <label className="compare-check">
            <input
              type="checkbox"
              checked={comparisonRunIds.includes(run.run_id)}
              disabled={!run.ligand_inputs[0]}
              onChange={() => onToggleComparison(run.run_id)}
            />
            Compare
          </label>
        </article>
      ))}
    </div>
  );
}
