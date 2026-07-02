import type { TriageFlags as TriageFlagsType } from '../types/candidate';

type TriageFlagsProps = {
  flags: TriageFlagsType | null;
};

export function TriageFlags({ flags }: TriageFlagsProps) {
  if (!flags) {
    return <p className="muted">No triage flags available.</p>;
  }

  const notes = [...flags.lipinski_notes, ...flags.veber_notes];
  const totalViolations = flags.lipinski_violations + flags.veber_violations;

  return (
    <div className="triage">
      <div className={totalViolations === 0 ? 'flag-pill pass' : 'flag-pill warn'}>
        {totalViolations === 0 ? 'No rule flags' : `${totalViolations} rule flags`}
      </div>
      {notes.length > 0 ? (
        <ul className="notes-list">
          {notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">Lipinski and Veber-style checks did not flag this candidate.</p>
      )}
    </div>
  );
}
