import { apiClient } from "@/api/client";
import type { Product, ProductCreateInput, ProductUpdateInput } from "@/types/api";

export interface ListProductsParams {
  search?: string;
  category?: string;
  low_stock?: boolean;
  overstock?: boolean;
  limit?: number;
  offset?: number;
}

export async function listProducts(params: ListProductsParams = {}): Promise<Product[]> {
  const { data } = await apiClient.get<Product[]>("/products", { params });
  return data;
}

export async function getProduct(id: string): Promise<Product> {
  const { data } = await apiClient.get<Product>(`/products/${id}`);
  return data;
}

export async function createProduct(input: ProductCreateInput): Promise<Product> {
  const { data } = await apiClient.post<Product>("/products", input);
  return data;
}

export async function updateProduct(id: string, input: ProductUpdateInput): Promise<Product> {
  const { data } = await apiClient.put<Product>(`/products/${id}`, input);
  return data;
}

export async function deleteProduct(id: string): Promise<void> {
  await apiClient.delete(`/products/${id}`);
}
