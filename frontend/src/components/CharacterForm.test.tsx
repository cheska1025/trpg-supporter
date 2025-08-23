import { render } from '@testing-library/react';
import { withClient } from '@/test/utils';   // 추가

import { CharacterForm } from './CharacterForm';

describe('CharacterForm', () => {
  it('renders', () => {
    const { container } = render(
      withClient(<CharacterForm onSubmit={async () => {}} />)
    );
    expect(container).toMatchSnapshot();
  });
});
