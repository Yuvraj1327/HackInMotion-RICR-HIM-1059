import { apiClient } from "@/api/client";
import type { CSVImportResult, Sale, SaleCreateInput } from "@/types/api";

export interface ListSalesParams {
  product_id?: string;
  limit?: number;
  offset?: number;
}

export async function listSales(params: ListSalesParams = {}): Promise<Sale[]> {
  const { data } = await apiClient.get<Sale[]>("/sales", { params });
  return data;
}

export async function createSale(input: SaleCreateInput): Promise<Sale> {
  const { data } = await apiClient.post<Sale>("/sales", input);
  return data;
}

/**
 * The backend returns HTTP 200 even when the import itself failed
 * (e.g. missing CSV columns) - it signals failure via `success: false`
 * in the JSON body, not the HTTP status. Callers must check
 * `result.success`, not just whether the request resolved.
 */
export async function uploadSalesCsv(file: File): Promise<CSVImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<CSVImportResult>("/sales/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
