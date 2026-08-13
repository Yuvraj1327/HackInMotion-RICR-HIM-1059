///inventory.tsx
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, Search, Pencil, Trash2, Package, ChevronRight } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { ProductStatusBadge, deriveProductStatus } from "@/components/common/StatusBadges";
import { ProductFormModal } from "@/components/inventory/ProductFormModal";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { GenerateDemoDialog } from "@/components/dashboard/GenerateDemoDialog";
import { deleteProduct, listProducts } from "@/api/products";
import { listSuppliers } from "@/api/suppliers";
import { listStockoutPredictions, listOverstockAnalyses } from "@/api/inventory";
import { QUERY_KEYS } from "@/lib/constants";
import { debounce, formatCurrencyFull } from "@/lib/utils";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { Product, StockoutPrediction } from "@/types/api";

type StatusFilter = "all" | "healthy" | "low_stock" | "critical" | "overstock";

export default function Inventory() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [demoOpen, setDemoOpen] = useState(false);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  const debouncedSetSearch = useMemo(() => debounce((v: string) => setSearch(v), 350), []);

  const productsQuery = useQuery({
    queryKey: [...QUERY_KEYS.products, search, category],
    queryFn: () => listProducts({ search: search || undefined, category: category || undefined }),
  });

  const suppliersQuery = useQuery({ queryKey: QUERY_KEYS.suppliers, queryFn: listSuppliers });
  const stockoutQuery = useQuery({ queryKey: QUERY_KEYS.stockout(), queryFn: listStockoutPredictions });
  const overstockQuery = useQuery({ queryKey: QUERY_KEYS.overstock(), queryFn: listOverstockAnalyses });

  const supplierMap = useMemo(() => {
    const map = new Map<string, string>();
    suppliersQuery.data?.forEach((s) => map.set(s.id, s.name));
    return map;
  }, [suppliersQuery.data]);

  const stockoutMap = useMemo(() => {
    const map = new Map<string, StockoutPrediction>();
    stockoutQuery.data?.forEach((s) => map.set(s.product_id, s));
    return map;
  }, [stockoutQuery.data]);

  const overstockMap = useMemo(() => {
    const map = new Map<string, boolean>();
    overstockQuery.data?.forEach((o) => map.set(o.product_id, o.overstock));
    return map;
  }, [overstockQuery.data]);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.products });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
      toast({ variant: "success", title: "Product deleted" });
      setDeletingProduct(null);
    },
    onError: (err) => {
      toast({
        variant: "error",
        title: "Could not delete product",
        description: err instanceof ApiError ? err.message : undefined,
      });
    },
  });

  const categories = useMemo(() => {
    const set = new Set<string>();
    productsQuery.data?.forEach((p) => set.add(p.category));
    return Array.from(set);
  }, [productsQuery.data]);

  const filteredProducts = useMemo(() => {
    if (!productsQuery.data) return [];
    if (statusFilter === "all") return productsQuery.data;
    return productsQuery.data.filter((p) => {
      const status = deriveProductStatus(stockoutMap.get(p.id)?.stockout_risk, overstockMap.get(p.id));
      return status === statusFilter;
    });
  }, [productsQuery.data, statusFilter, stockoutMap, overstockMap]);

  const isLoading = productsQuery.isLoading;

  return (
    <AppShell title="Inventory">
      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 flex-col gap-3 sm:flex-row">
            <div className="relative flex-1 sm:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search by name or SKU..."
                value={searchInput}
                onChange={(e) => {
                  setSearchInput(e.target.value);
                  debouncedSetSearch(e.target.value);
                }}
                aria-label="Search products"
              />
            </div>
            <Select
              className="sm:w-40"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              aria-label="Filter by category"
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
            <Select
              className="sm:w-40"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              aria-label="Filter by status"
            >
              <option value="all">All statuses</option>
              <option value="healthy">🟢 Healthy</option>
              <option value="low_stock">🟡 Low Stock</option>
              <option value="critical">🔴 Critical</option>
              <option value="overstock">🟣 Overstock</option>
            </Select>
          </div>
          <Button
            onClick={() => {
              setEditingProduct(null);
              setFormOpen(true);
            }}
          >
            <Plus className="h-4 w-4" />
            Add Product
          </Button>
        </div>

        {isLoading && (
          <Card>
            <div className="space-y-3 p-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          </Card>
        )}

        {productsQuery.isError && (
          <ErrorState
            message={
              productsQuery.error instanceof ApiError ? productsQuery.error.message : "Unable to load products."
            }
            onRetry={() => productsQuery.refetch()}
          />
        )}

        {!isLoading && !productsQuery.isError && filteredProducts.length === 0 && (
          <EmptyState
            icon={<Package className="h-10 w-10" />}
            title={productsQuery.data?.length === 0 ? "No products yet" : "No products match your filters"}
            description={
              productsQuery.data?.length === 0
                ? "Add your first product or generate a demo store to get started."
                : "Try adjusting your search or filters."
            }
            action={
              productsQuery.data?.length === 0 ? (
                <div className="flex gap-2">
                  <Button onClick={() => setFormOpen(true)}>
                    <Plus className="h-4 w-4" /> Add Product
                  </Button>
                  <Button variant="outline" onClick={() => setDemoOpen(true)}>
                    Generate Demo Store
                  </Button>
                </div>
              ) : undefined
            }
          />
        )}

        {!isLoading && filteredProducts.length > 0 && (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full min-w-[860px] text-sm">
                <thead className="border-b border-border bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Product</th>
                    <th className="px-4 py-3 font-medium">SKU</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 font-medium">Stock</th>
                    <th className="px-4 py-3 font-medium">Price</th>
                    <th className="px-4 py-3 font-medium">Supplier</th>
                    <th className="px-4 py-3 font-medium">Lead Time</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredProducts.map((product) => {
                    const status = deriveProductStatus(
                      stockoutMap.get(product.id)?.stockout_risk,
                      overstockMap.get(product.id)
                    );
                    return (
                      <tr key={product.id} className="hover:bg-muted/30">
                        <td className="px-4 py-3">
                          <Link
                            to={`/inventory/${product.id}`}
                            className="flex items-center gap-1 font-medium text-foreground hover:text-primary"
                          >
                            {product.name}
                            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{product.sku}</td>
                        <td className="px-4 py-3 text-muted-foreground">{product.category}</td>
                        <td className="px-4 py-3 text-foreground">
                          {product.current_stock} {product.unit}
                        </td>
                        <td className="px-4 py-3 text-foreground">{formatCurrencyFull(product.price)}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {product.supplier_id ? supplierMap.get(product.supplier_id) ?? "—" : "—"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{product.lead_time_days}d</td>
                        <td className="px-4 py-3">
                          <ProductStatusBadge status={status} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label={`Edit ${product.name}`}
                              onClick={() => {
                                setEditingProduct(product);
                                setFormOpen(true);
                              }}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label={`Delete ${product.name}`}
                              onClick={() => setDeletingProduct(product)}
                            >
                              <Trash2 className="h-4 w-4 text-critical" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      <ProductFormModal
        open={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingProduct(null);
        }}
        product={editingProduct}
      />

      <ConfirmDialog
        open={!!deletingProduct}
        onClose={() => setDeletingProduct(null)}
        onConfirm={() => deletingProduct && deleteMutation.mutate(deletingProduct.id)}
        title="Delete product"
        description={`Are you sure you want to delete "${deletingProduct?.name}"? This cannot be undone.`}
        isLoading={deleteMutation.isPending}
      />

      <GenerateDemoDialog open={demoOpen} onClose={() => setDemoOpen(false)} />
    </AppShell>
  );
}
