type Molecule2DProps = {
  svg: string | null;
  name: string;
};

export function Molecule2D({ svg, name }: Molecule2DProps) {
  if (!svg) {
    return <div className="empty-structure">No 2D structure available.</div>;
  }

  return (
    <div
      className="molecule-2d"
      role="img"
      aria-label={`2D structure of ${name}`}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
