import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { CharactersTable } from './CharactersTable';
import { withClient } from '@/test/utils';
import type { Character } from '@/types/characters';

describe('CharactersTable', () => {
  it('renders empty', () => {
    const { container } = render(withClient(
      <CharactersTable items={[]} onEdit={() => {}} onDelete={() => {}} />
    ));
    expect(container).toBeTruthy();
  });

  it('renders some rows', () => {
    const items: Character[] = [{ id: 1, name: 'A', clazz: 'W', level: 1 }];
    const { getByText } = render(withClient(
      <CharactersTable items={items} onEdit={() => {}} onDelete={() => {}} />
    ));
    expect(getByText('A')).toBeInTheDocument();
  });
});
