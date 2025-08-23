import type { Character } from '@/types/characters';

type Props = {
  items: Character[];
  onDelete?: (id: number) => void;
  onEdit?: (id: number, patch: Partial<Pick<Character, 'name' | 'clazz' | 'level'>>) => void;
};

export function CharactersTable({ items, onDelete, onEdit }: Props) {
  return (
    <table>
      <thead>
        <tr>
          <th>ID ▾</th>
          <th>Name</th>
          <th>Class</th>
          <th>Level</th>
          {(onDelete || onEdit) && <th>Actions</th>}
        </tr>
      </thead>
      <tbody>
        {items.length === 0 ? (
          <tr>
            <td colSpan={5} style={{ textAlign: 'center' }}>
              No data
            </td>
          </tr>
        ) : (
          items.map((c) => (
            <tr key={c.id}>
              <td>{c.id}</td>
              <td>{c.name}</td>
              <td>{c.clazz}</td>
              <td>{c.level}</td>
              {(onDelete || onEdit) && (
                <td>
                  {onEdit && (
                    <button onClick={() => onEdit(c.id, { level: c.level + 1 })}>+1 Lv</button>
                  )}
                  {onDelete && <button onClick={() => onDelete(c.id)}>Delete</button>}
                </td>
              )}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
