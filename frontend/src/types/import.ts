export interface ImportJobOut {
  id: string;
  original_filename: string;
  status: 'uploaded' | 'mapped' | 'importing' | 'imported' | 'failed';
  created_by: string;
  total_rows: number;
  success_rows: number;
  error_rows: number;
  column_mapping: Record<string, string> | null;
  file_path: string;
  created_at: string;
  updated_at: string | null;
}

export interface ImportErrorOut {
  id: string;
  import_job_id: string;
  row_number: number;
  raw_data: Record<string, string | null> | null;
  error_messages: string[];
  field_name: string | null;
  created_at: string;
}

export interface ImportJobDetail extends ImportJobOut {
  errors: ImportErrorOut[];
}

export interface ColumnInfo {
  header: string;
  auto_detected_field: string | null;
}

export interface ColumnsResponse {
  columns: ColumnInfo[];
  sheet_names: string[];
  total_rows: number;
}

export interface PreviewRow {
  row_number: number;
  data: Record<string, string | null>;
  errors: string[];
}

export interface PreviewResponse {
  columns: ColumnInfo[];
  rows: PreviewRow[];
  total_rows: number;
  preview_count: number;
}

export interface ImportResult {
  import_job_id: string;
  total_rows: number;
  success_rows: number;
  error_rows: number;
  status: string;
}

export interface FieldMappingRequest {
  mapping: Record<string, string>;
}

export interface ImportConfirmRequest {
  overwrite_existing: boolean;
}
