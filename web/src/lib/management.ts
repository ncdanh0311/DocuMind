import type { DocumentItem, Notebook } from '@/types';

export type SortOrder = 'newest' | 'oldest' | 'name';
export function documentStatusLabel(status: string, aiEnabled: boolean): string {
  if (status === 'error') return 'Lỗi xử lý';
  if (status === 'ready') return 'Sẵn sàng';
  if (status === 'processing') return aiEnabled ? 'Đang xử lý' : 'Xử lý đang tạm hoãn';
  return aiEnabled ? 'Đang chờ xử lý' : 'Đã lưu';
}
export const CATEGORY_LABELS = { study: 'Học tập', project: 'Dự án', research: 'Nghiên cứu', personal: 'Cá nhân' };
export function searchKey(value: string): string {
  return value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').trim().replace(/\s+/g, ' ');
}
function ordered<T>(rows: T[], sort: SortOrder, name: (row: T) => string, date: (row: T) => string | undefined, id: (row: T) => string): T[] {
  const compare = (a: string, b: string) => a < b ? -1 : a > b ? 1 : 0;
  return rows.sort((a, b) => {
    const value = sort === 'name' ? compare(searchKey(name(a)), searchKey(name(b)))
      : ((Date.parse(date(a) || '') || 0) - (Date.parse(date(b) || '') || 0)) * (sort === 'newest' ? -1 : 1);
    return value || compare(id(a), id(b));
  });
}
export function selectNotebooks(rows: Notebook[], query = '', category = 'all', sort: SortOrder = 'newest'): Notebook[] {
  const key = searchKey(query);
  return ordered(rows.filter((row) => (category === 'all' || row.category === category)
    && searchKey(`${row.title} ${row.description || ''}`).includes(key)), sort, row => row.title, row => row.created_at, row => row.notebook_id);
}
export function selectDocuments(rows: DocumentItem[], query = '', extension = 'all', status = 'all', sort: SortOrder = 'newest'): DocumentItem[] {
  return ordered(rows.filter((row) => searchKey(row.file_name).includes(searchKey(query))
    && (extension === 'all' || row.file_name.split('.').pop()?.toLowerCase() === extension)
    && (status === 'all' || row.status === status)), sort, row => row.file_name, row => row.uploaded_at, row => row.document_id);
}
