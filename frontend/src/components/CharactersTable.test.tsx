import { describe, it, expect } from 'vitest';
import { render, within } from '@testing-library/react';
import { withClient } from '@/test/utils';
import { CharactersTable } from './CharactersTable';
import type { Character } from '@/types/characters';

describe('CharactersTable', () => {
  it('renders empty', () => {
    const { container, getByText } = render(
      withClient(<CharactersTable items={[]} onEdit={() => {}} onDelete={() => {}} />)
    );
    expect(getByText(/No data/i)).toBeInTheDocument();
  });

  it('renders some rows', () => {
    const items: Character[] = [{ id: 1, name: 'A', clazz: 'W', level: 1 }];
    const { container } = render(
      withClient(<CharactersTable items={items} onEdit={() => {}} onDelete={() => {}} />)
    );

    const tbody = container.querySelector('tbody')!;
    expect(within(tbody).getByText('A')).toBeInTheDocument();
    expect(within(tbody).getByText('W')).toBeInTheDocument();
  });
});
