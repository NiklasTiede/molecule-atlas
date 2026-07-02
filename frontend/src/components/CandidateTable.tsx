import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import type { ColumnDef, SortingState } from '@tanstack/react-table';
import { useMemo, useState } from 'react';

import type { Candidate } from '../types/candidate';

type CandidateTableProps = {
  candidates: Candidate[];
  selectedId: string | null;
  onSelect: (candidateId: string) => void;
};

function formatNumber(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) {
    return '-';
  }
  return value.toFixed(digits);
}

export function CandidateTable({ candidates, selectedId, onSelect }: CandidateTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [validOnly, setValidOnly] = useState(false);

  const filteredCandidates = useMemo(() => {
    return validOnly ? candidates.filter((candidate) => candidate.is_valid) : candidates;
  }, [candidates, validOnly]);

  const columns = useMemo<ColumnDef<Candidate>[]>(
    () => [
      {
        id: 'state',
        header: 'State',
        cell: ({ row }) => (
          <span
            className={row.original.is_valid ? 'status-dot valid' : 'status-dot invalid'}
            aria-label={row.original.is_valid ? 'Valid molecule' : 'Invalid molecule'}
          />
        ),
        enableSorting: false,
      },
      {
        accessorKey: 'name',
        header: 'Name',
      },
      {
        accessorKey: 'score',
        header: 'Score',
        cell: ({ row }) => formatNumber(row.original.score, 1),
      },
      {
        id: 'molecular_weight',
        header: 'MW',
        accessorFn: (candidate) => candidate.descriptors?.molecular_weight ?? null,
        cell: ({ row }) => formatNumber(row.original.descriptors?.molecular_weight, 1),
      },
      {
        id: 'logp',
        header: 'LogP',
        accessorFn: (candidate) => candidate.descriptors?.logp ?? null,
        cell: ({ row }) => formatNumber(row.original.descriptors?.logp, 2),
      },
      {
        id: 'tpsa',
        header: 'TPSA',
        accessorFn: (candidate) => candidate.descriptors?.tpsa ?? null,
        cell: ({ row }) => formatNumber(row.original.descriptors?.tpsa, 1),
      },
      {
        id: 'hbond_donors',
        header: 'HBD',
        accessorFn: (candidate) => candidate.descriptors?.hbond_donors ?? null,
      },
      {
        id: 'hbond_acceptors',
        header: 'HBA',
        accessorFn: (candidate) => candidate.descriptors?.hbond_acceptors ?? null,
      },
      {
        id: 'rotatable_bonds',
        header: 'RotB',
        accessorFn: (candidate) => candidate.descriptors?.rotatable_bonds ?? null,
      },
      {
        id: 'lipinski',
        header: 'Lip.',
        accessorFn: (candidate) => candidate.triage_flags?.lipinski_violations ?? null,
      },
      {
        id: 'scaffold',
        header: 'Scaffold',
        accessorFn: (candidate) => candidate.descriptors?.murcko_scaffold ?? 'Invalid',
      },
    ],
    [],
  );

  const table = useReactTable({
    data: filteredCandidates,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    globalFilterFn: (row, _columnId, filterValue) => {
      const query = String(filterValue).toLowerCase();
      return (
        row.original.name.toLowerCase().includes(query) ||
        row.original.smiles.toLowerCase().includes(query) ||
        (row.original.canonical_smiles?.toLowerCase().includes(query) ?? false)
      );
    },
  });

  return (
    <section className="table-panel" aria-label="Candidate table">
      <div className="toolbar">
        <input
          aria-label="Search by name or SMILES"
          placeholder="Search by name or SMILES"
          value={globalFilter}
          onChange={(event) => setGlobalFilter(event.target.value)}
        />
        <label className="toggle">
          <input
            type="checkbox"
            checked={validOnly}
            onChange={(event) => setValidOnly(event.target.checked)}
          />
          Valid only
        </label>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id}>
                    {header.isPlaceholder ? null : (
                      <button
                        className="column-header"
                        type="button"
                        disabled={!header.column.getCanSort()}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{
                          asc: '▲',
                          desc: '▼',
                        }[header.column.getIsSorted() as string] ?? null}
                      </button>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                className={[
                  row.original.id === selectedId ? 'selected' : '',
                  row.original.is_valid ? '' : 'invalid-row',
                ]
                  .filter(Boolean)
                  .join(' ')}
                key={row.id}
                onClick={() => onSelect(row.original.id)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
