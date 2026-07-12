import { useCallback, useEffect, useMemo, useState, type ChangeEvent } from 'react';

import {
  compareCandidateEvidence,
  fetchCandidateEvidence,
  fetchEvidenceArtifacts,
  fetchEvidenceReport,
  fetchEvidenceRun,
  fetchEvidenceRuns,
  fetchEvidenceValidation,
  importEvidenceBundle,
} from '../../api/evidence';
import type {
  ArtifactInventory,
  CandidateEvidence,
  EvidenceComparison,
  EvidenceRunSummary,
  EvidenceValidation,
} from '../../types/evidence';
import { EvidenceComparison as EvidenceComparisonPanel } from './EvidenceComparison';
import { EvidenceRunDetail } from './EvidenceRunDetail';
import { EvidenceRunList } from './EvidenceRunList';

interface DetailData {
  run: EvidenceRunSummary;
  candidateEvidence: CandidateEvidence | null;
  artifacts: ArtifactInventory;
  validation: EvidenceValidation;
}

function downloadReport(filename: string, content: string, mediaType: string) {
  const url = URL.createObjectURL(new Blob([content], { type: mediaType }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function idempotencyKey() {
  return typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `evidence-import-${Date.now()}`;
}

export function EvidenceWorkbench() {
  const [runs, setRuns] = useState<EvidenceRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DetailData | null>(null);
  const [comparisonRunIds, setComparisonRunIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<EvidenceComparison | null>(null);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [reportPending, setReportPending] = useState(false);
  const [comparisonPending, setComparisonPending] = useState(false);
  const [importPending, setImportPending] = useState(false);

  const refreshRuns = useCallback(async (selectRunId?: string) => {
    setLoadingRuns(true);
    setError(null);
    try {
      const result = await fetchEvidenceRuns();
      setRuns(result.runs);
      setSelectedRunId((current) => {
        if (selectRunId && result.runs.some((run) => run.run_id === selectRunId)) {
          return selectRunId;
        }
        return current && result.runs.some((run) => run.run_id === current)
          ? current
          : (result.runs[0]?.run_id ?? null);
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load evidence runs.');
    } finally {
      setLoadingRuns(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => refreshRuns());
  }, [refreshRuns]);

  useEffect(() => {
    if (!selectedRunId) {
      return;
    }
    let active = true;
    void Promise.resolve().then(async () => {
      setLoadingDetail(true);
      setError(null);
      try {
        const run = await fetchEvidenceRun(selectedRunId);
        const ligand = run.ligand_inputs[0];
        const [artifacts, validation, candidateEvidence] = await Promise.all([
          fetchEvidenceArtifacts(run.run_id),
          fetchEvidenceValidation(run.run_id),
          ligand ? fetchCandidateEvidence(run.run_id, ligand.upstream_id ?? ligand.input_id) : Promise.resolve(null),
        ]);
        if (active) {
          setDetail({ run, artifacts, validation, candidateEvidence });
        }
      } catch (caught) {
        if (active) {
          setDetail(null);
          setError(caught instanceof Error ? caught.message : 'Could not load evidence run details.');
        }
      } finally {
        if (active) {
          setLoadingDetail(false);
        }
      }
    });
    return () => {
      active = false;
    };
  }, [selectedRunId]);

  const selectedRuns = useMemo(
    () => runs.filter((run) => comparisonRunIds.includes(run.run_id)),
    [comparisonRunIds, runs],
  );

  function toggleComparison(runId: string) {
    setComparison(null);
    setComparisonRunIds((current) => {
      if (current.includes(runId)) {
        return current.filter((id) => id !== runId);
      }
      return current.length >= 10 ? current : [...current, runId];
    });
  }

  async function runComparison() {
    if (selectedRuns.length < 2) {
      setNotice('Select at least two runs with recorded ligand inputs to compare evidence.');
      return;
    }
    setComparisonPending(true);
    setNotice(null);
    try {
      const result = await compareCandidateEvidence({
        contract_version: '0.1.0',
        subjects: selectedRuns.map((run) => {
          const ligand = run.ligand_inputs[0]!;
          return {
            subject_id: run.run_id,
            label: run.method.upstream_tool ?? run.run_id,
            run_id: run.run_id,
            candidate_id: ligand.upstream_id ?? ligand.input_id,
            candidate_external_id: null,
          };
        }),
      });
      setComparison(result);
    } catch (caught) {
      setNotice(caught instanceof Error ? caught.message : 'Could not compare evidence.');
    } finally {
      setComparisonPending(false);
    }
  }

  async function report(format: 'markdown' | 'html') {
    if (!detail) return;
    setReportPending(true);
    setNotice(null);
    try {
      const result = await fetchEvidenceReport(detail.run.run_id, format);
      downloadReport(result.filename, result.content, result.media_type);
      setNotice(`${format === 'html' ? 'HTML' : 'Markdown'} report prepared for download.`);
    } catch (caught) {
      setNotice(caught instanceof Error ? caught.message : 'Could not create the report.');
    } finally {
      setReportPending(false);
    }
  }

  async function handleImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setImportPending(true);
    setNotice(null);
    try {
      const result = await importEvidenceBundle(file, idempotencyKey());
      await refreshRuns(result.run.run_id);
      setNotice(`Imported evidence run ${result.run.run_id}.`);
    } catch (caught) {
      setNotice(caught instanceof Error ? caught.message : 'Could not import the evidence bundle.');
    } finally {
      setImportPending(false);
    }
  }

  return (
    <section className="evidence-workbench" aria-label="Evidence Runs workspace">
      <header className="evidence-workbench-header">
        <div>
          <p className="eyebrow">Portable, inspectable evidence</p>
          <h1>Evidence Runs</h1>
          <p>Review typed predictions, validation, artifacts, and recorded provenance.</p>
        </div>
        <label className={`upload-action ${importPending ? 'pending' : ''}`}>
          <input type="file" accept=".zip,application/zip" onChange={handleImport} disabled={importPending} />
          {importPending ? 'Importing…' : 'Import evidence bundle'}
        </label>
      </header>

      {notice && <p className="notice-banner">{notice}</p>}
      {error && <p className="error-banner">{error}</p>}
      <div className="evidence-layout">
        <aside className="evidence-sidebar">
          <div className="sidebar-title">
            <h2>Available runs</h2>
            <span>{runs.length}</span>
          </div>
          {loadingRuns ? <p className="muted">Loading evidence runs…</p> : (
            runs.length ? (
              <EvidenceRunList
                runs={runs}
                selectedRunId={selectedRunId}
                comparisonRunIds={comparisonRunIds}
                onSelect={setSelectedRunId}
                onToggleComparison={toggleComparison}
              />
            ) : (
              <div className="empty-evidence">
                <strong>No evidence runs are available yet.</strong>
                <span>Import a portable evidence bundle to begin review.</span>
              </div>
            )
          )}
          {comparisonRunIds.length > 0 && (
            <div className="comparison-controls">
              <strong>{comparisonRunIds.length} selected for comparison</strong>
              <button type="button" onClick={runComparison} disabled={comparisonRunIds.length < 2 || comparisonPending}>
                {comparisonPending ? 'Comparing…' : 'Compare selected'}
              </button>
            </div>
          )}
        </aside>
        <div className="evidence-main">
          {loadingDetail && <p className="muted">Loading run evidence…</p>}
          {!loadingDetail && detail && runs.length > 0 && (
            <EvidenceRunDetail
              run={detail.run}
              candidateEvidence={detail.candidateEvidence}
              artifacts={detail.artifacts}
              validation={detail.validation}
              onReport={report}
              reportPending={reportPending}
            />
          )}
          {!loadingDetail && !detail && runs.length > 0 && !error && (
            <p className="muted">Choose an evidence run to begin review.</p>
          )}
          <EvidenceComparisonPanel comparison={comparison} />
        </div>
      </div>
    </section>
  );
}
