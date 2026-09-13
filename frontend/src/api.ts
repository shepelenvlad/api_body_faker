export interface SchemaInfo {
  id: string;
  title: string;
  description: string;
}

const BASE_URL = '/api';

export async function fetchSchemas(): Promise<SchemaInfo[]> {
  const res = await fetch(`${BASE_URL}/schemas`);
  if (!res.ok) throw new Error('Не удалось загрузить список схем');
  return res.json();
}

export async function generateBody(schemaId: string): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/generate/${schemaId}`);
  if (!res.ok) throw new Error('Не удалось сгенерировать тело запроса');
  return res.json();
}
