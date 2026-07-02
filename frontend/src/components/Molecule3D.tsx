import { useEffect, useRef } from 'react';

type Molecule3DProps = {
  molBlock: string | null;
};

export function Molecule3D({ molBlock }: Molecule3DProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current || !molBlock) {
      return;
    }

    let cancelled = false;
    const container = containerRef.current;
    container.innerHTML = '';

    void import('3dmol').then(({ createViewer }) => {
      if (cancelled) {
        return;
      }
      const viewer = createViewer(container, { backgroundColor: 'white' });
      viewer.addModel(molBlock, 'sdf');
      viewer.setStyle({}, { stick: {} });
      viewer.zoomTo();
      viewer.render();
    });

    return () => {
      cancelled = true;
      container.replaceChildren();
    };
  }, [molBlock]);

  if (!molBlock) {
    return <div className="empty-structure">Select a valid molecule to view a 3D conformer.</div>;
  }

  return <div ref={containerRef} className="molecule-3d" aria-label="3D conformer viewer" />;
}
