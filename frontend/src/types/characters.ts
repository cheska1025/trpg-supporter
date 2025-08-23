export type Character = {
  id: number;
  name: string;
  clazz: string;
  level: number;
};

export type CharacterIn = {
  name: string;
  clazz: string;
  level?: number;
};

export type CharacterListQuery = {
  name?: string;
  order_by?: "id" | "level";
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
};
