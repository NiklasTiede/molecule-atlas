import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { App } from './App';

describe('App', () => {
  it('renders the Molecule Atlas shell', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Molecule Atlas' })).toBeInTheDocument();
    expect(screen.getByText('Loading candidate set...')).toBeInTheDocument();
  });
});
