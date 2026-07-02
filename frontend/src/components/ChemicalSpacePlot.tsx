import Plot from 'react-plotly.js';

import type { ProjectionPoint } from '../types/candidate';

type ChemicalSpacePlotProps = {
  points: ProjectionPoint[];
  selectedId: string | null;
  onSelect: (candidateId: string) => void;
};

export function ChemicalSpacePlot({ points, selectedId, onSelect }: ChemicalSpacePlotProps) {
  if (points.length === 0) {
    return null;
  }

  return (
    <section className="plot-panel" aria-label="Chemical space">
      <div className="plot-header">
        <h2>Chemical Space</h2>
        <span>Morgan fingerprints · PCA</span>
      </div>
      <Plot
        data={[
          {
            x: points.map((point) => point.x),
            y: points.map((point) => point.y),
            text: points.map((point) => point.name),
            customdata: points.map((point) => point.candidate_id),
            mode: 'markers',
            type: 'scatter',
            marker: {
              size: points.map((point) => (point.candidate_id === selectedId ? 12 : 8)),
              color: points.map((point) =>
                point.candidate_id === selectedId ? '#146c5c' : '#7d8f89',
              ),
            },
          },
        ]}
        layout={{
          autosize: true,
          height: 280,
          margin: { l: 38, r: 16, t: 12, b: 38 },
          xaxis: { title: { text: 'PC1' } },
          yaxis: { title: { text: 'PC2' } },
        }}
        config={{ displayModeBar: false, responsive: true }}
        onClick={(event) => {
          const candidateId = event.points[0]?.customdata;
          if (typeof candidateId === 'string') {
            onSelect(candidateId);
          }
        }}
        useResizeHandler
        className="plot"
      />
    </section>
  );
}
