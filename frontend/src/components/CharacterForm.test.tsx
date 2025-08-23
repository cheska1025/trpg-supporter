import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { CharacterForm } from './CharacterForm';
import { withClient } from '@/test/utils';

describe('CharacterForm', () => {
  it('renders', () => {
    const { container } = render(withClient(
      <CharacterForm onSubmit={async () => {}} />
    ));
    expect(container).toBeTruthy();
  });
});
