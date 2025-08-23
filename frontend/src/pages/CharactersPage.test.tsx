import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CharactersPage from '@/pages/CharactersPage';
import { withClient } from '@/test/utils';

describe('CharactersPage (integration)', () => {
  it('lists, creates, updates, deletes characters with msw', async () => {
    render(withClient(<CharactersPage />));

    // 초기 목록: 비어있음
    await waitFor(() => {
      expect(screen.getByText(/characters/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole('row', { name: /alice/i })).not.toBeInTheDocument();

    // 생성
    await userEvent.type(screen.getByLabelText(/name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/class|clazz/i), 'Wizard');
    await userEvent.clear(screen.getByLabelText(/level/i));
    await userEvent.type(screen.getByLabelText(/level/i), '2');
    await userEvent.click(screen.getByRole('button', { name: /create/i }));

    // 테이블에 나타남
    await screen.findByText('Alice');
    expect(screen.getByText('Wizard')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();

    // 업데이트 (level +1 가정: Edit 버튼이 있고 입력/저장하는 UI라면 그에 맞게 조작)
    // 여기서는 간단히 "Edit" 버튼을 눌러 level을 3으로 바꾼다고 가정
    const editBtns = screen.getAllByRole('button', { name: /edit/i });
    await userEvent.click(editBtns[0]);

    const levelInput = screen.getByLabelText(/level/i);
    await userEvent.clear(levelInput);
    await userEvent.type(levelInput, '3');
    await userEvent.click(screen.getByRole('button', { name: /save/i }));

    await screen.findByText('3');

    // 삭제
    const delBtns = screen.getAllByRole('button', { name: /delete/i });
    await userEvent.click(delBtns[0]);

    await waitFor(() => {
      expect(screen.queryByText('Alice')).not.toBeInTheDocument();
    });
  });

  it('shows error on duplicate name (409)', async () => {
    render(withClient(<CharactersPage />));
    // 첫 생성
    await userEvent.type(screen.getByLabelText(/name/i), 'DupName');
    await userEvent.type(screen.getByLabelText(/class|clazz/i), 'Rogue');
    await userEvent.click(screen.getByRole('button', { name: /create/i }));
    await screen.findByText('DupName');

    // 중복 생성
    await userEvent.clear(screen.getByLabelText(/name/i));
    await userEvent.type(screen.getByLabelText(/name/i), 'DupName');
    await userEvent.click(screen.getByRole('button', { name: /create/i }));

    // 페이지/컴포넌트에서 409 detail을 메시지로 보여준다는 가정
    // (실 구현에 맞게 셀렉터나 문구를 조정하세요)
    await screen.findByText(/already exists/i);
  });
});
