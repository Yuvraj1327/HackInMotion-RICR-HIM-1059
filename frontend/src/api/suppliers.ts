import { apiClient } from "@/api/client";
import type { Supplier, SupplierCreateInput, SupplierUpdateInput } from "@/types/api";

export async function listSuppliers(): Promise<Supplier[]> {
  const { data } = await apiClient.get<Supplier[]>("/suppliers");
  return data;
}

export async function getSupplier(id: string): Promise<Supplier> {
  const { data } = await apiClient.get<Supplier>(`/suppliers/${id}`);
  return data;
}

export async function createSupplier(input: SupplierCreateInput): Promise<Supplier> {
  const { data } = await apiClient.post<Supplier>("/suppliers", input);
  return data;
}

export async function updateSupplier(id: string, input: SupplierUpdateInput): Promise<Supplier> {
  const { data } = await apiClient.put<Supplier>(`/suppliers/${id}`, input);
  return data;
}

export async function deleteSupplier(id: string): Promise<void> {
  await apiClient.delete(`/suppliers/${id}`);
}
