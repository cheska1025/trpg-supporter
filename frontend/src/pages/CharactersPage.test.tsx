import { describe, it, expect } from 'vitest';
import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/utils';
import CharactersPage from './CharactersPage';

describe('CharactersPage (integration)', () => {
  it('lists, creates, promotes(+1 Lv), deletes characters with msw', async () => {
    renderWithProviders(<CharactersPage />);
    const user = userEvent.setup();

    // 1) 초기 렌더 & 목록 데이터 확인 (MSW 시드: Alice/Bob/Charlie)
    await screen.findByRole('heading', { name: /characters/i });
    await screen.findByText(/alice/i);
    await screen.findByText(/bob/i);
    await screen.findByText(/charlie/i);

    // 2) 생성(Create) — 섹션을 기준으로 폼 조작
    const createSection = screen.getByRole('region', { name: /create character/i });
    const nameInput = within(createSection).getByLabelText(/name/i);
    const classInput = within(createSection).getByLabelText(/class/i);
    const levelInput = within(createSection).getByLabelText(/level/i);
    const createButton = within(createSection).getByRole('button', { name: /create/i });

    await user.clear(nameInput);
    await user.type(nameInput, 'Dave');
    await user.clear(classInput);
    await user.type(classInput, 'Fighter');
    await user.clear(levelInput);
    await user.type(levelInput, '3');
    await user.click(createButton);

    // 생성 후 목록에 Dave 등장
    const daveCell = await screen.findByText(/dave/i);
    expect(daveCell).toBeInTheDocument();

    // Dave 행을 잡아서 그 안의 버튼/값만 검사
    const daveRow = daveCell.closest('tr') as HTMLTableRowElement;
    expect(daveRow).toBeTruthy();

    // 3) 레벨업(+1 Lv) — 생성 시 3 → 클릭 후 4로 변해야 함
    const promoteBtn = within(daveRow).getByRole('button', { name: /\+1 lv/i });
    await user.click(promoteBtn);

    // 같은 행에서 "Level" 셀(인덱스 3)만 정확히 확인 (0:ID, 1:Name, 2:Class, 3:Level)
    const cells = within(daveRow).getAllByRole('cell');
    expect(cells[3]).toHaveTextContent('4');

    // 4) 삭제(Delete) — 행의 Delete 버튼 클릭 후 Dave가 사라져야 함
    const deleteBtn = within(daveRow).getByRole('button', { name: /delete/i });
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(screen.queryByText(/dave/i)).not.toBeInTheDocument();
    });
  });
});
