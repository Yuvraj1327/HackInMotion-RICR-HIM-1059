import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Select } from "@/components/ui/Select";
import { createProduct, updateProduct } from "@/api/products";
import { listSuppliers } from "@/api/suppliers";
import { QUERY_KEYS } from "@/lib/constants";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { Product } from "@/types/api";

interface ProductFormModalProps {
  open: boolean;
  onClose: () => void;
  product?: Product | null;
}

interface FormState {
  name: string;
  sku: string;
  category: string;
  current_stock: string;
  price: string;
  cost_price: string;
  supplier_id: string;
  lead_time_days: string;
  safety_stock: string;
  unit: string;
}

const EMPTY_FORM: FormState = {
  name: "",
  sku: "",
  category: "",
  current_stock: "",
  price: "",
  cost_price: "",
  supplier_id: "",
  lead_time_days: "3",
  safety_stock: "0",
  unit: "unit",
};

export function ProductFormModal({ open, onClose, product }: ProductFormModalProps) {
  const isEdit = !!product;
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [validationError, setValidationError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: suppliers } = useQuery({
    queryKey: QUERY_KEYS.suppliers,
    queryFn: listSuppliers,
    enabled: open,
  });

  useEffect(() => {
    if (!open) return;
    if (product) {
      setForm({
        name: product.name,
        sku: product.sku,
        category: product.category,
        current_stock: String(product.current_stock),
        price: String(product.price),
        cost_price: String(product.cost_price),
        supplier_id: product.supplier_id ?? "",
        lead_time_days: String(product.lead_time_days),
        safety_stock: String(product.safety_stock),
        unit: product.unit,
      });
    } else {
      setForm(EMPTY_FORM);
    }
    setValidationError(null);
  }, [open, product]);

  const mutation = useMutation({
    mutationFn: async () => {
      const current_stock = Number(form.current_stock);
      const price = Number(form.price);
      const cost_price = Number(form.cost_price);
      const lead_time_days = Number(form.lead_time_days);
      const safety_stock = Number(form.safety_stock);

      if (current_stock < 0 || price <= 0 || cost_price <= 0 || lead_time_days < 0 || safety_stock < 0) {
        throw new ApiError(
          "Stock, lead time, and safety stock cannot be negative, and prices must be greater than zero.",
          null,
          "client_validation"
        );
      }

      const payload = {
        name: form.name.trim(),
        sku: form.sku.trim(),
        category: form.category.trim(),
        current_stock,
        price,
        cost_price,
        supplier_id: form.supplier_id || null,
        lead_time_days,
        safety_stock,
        unit: form.unit.trim() || "unit",
      };

      if (isEdit && product) {
        return updateProduct(product.id, payload);
      }
      return createProduct(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.products });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
      toast({
        variant: "success",
        title: isEdit ? "Product updated" : "Product created",
        description: `${form.name} was saved successfully.`,
      });
      onClose();
    },
    onError: (err) => {
      setValidationError(err instanceof ApiError ? err.message : "Unable to save product.");
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setValidationError(null);
    mutation.mutate();
  }

  function set<K extends keyof FormState>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? "Edit Product" : "Add Product"}
      description={isEdit ? "Update this product's details." : "Add a new product to your catalog."}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="name">Product name</Label>
            <Input id="name" required value={form.name} onChange={(e) => set("name", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="sku">SKU</Label>
            <Input id="sku" required value={form.sku} onChange={(e) => set("sku", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="category">Category</Label>
            <Input id="category" required value={form.category} onChange={(e) => set("category", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="current_stock">Current stock</Label>
            <Input
              id="current_stock"
              type="number"
              min={0}
              required
              value={form.current_stock}
              onChange={(e) => set("current_stock", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="unit">Unit</Label>
            <Input id="unit" value={form.unit} onChange={(e) => set("unit", e.target.value)} placeholder="unit" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="price">Selling price (₹)</Label>
            <Input
              id="price"
              type="number"
              min={0.01}
              step="0.01"
              required
              value={form.price}
              onChange={(e) => set("price", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cost_price">Cost price (₹)</Label>
            <Input
              id="cost_price"
              type="number"
              min={0.01}
              step="0.01"
              required
              value={form.cost_price}
              onChange={(e) => set("cost_price", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="lead_time_days">Lead time (days)</Label>
            <Input
              id="lead_time_days"
              type="number"
              min={0}
              max={365}
              required
              value={form.lead_time_days}
              onChange={(e) => set("lead_time_days", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="safety_stock">Safety stock</Label>
            <Input
              id="safety_stock"
              type="number"
              min={0}
              required
              value={form.safety_stock}
              onChange={(e) => set("safety_stock", e.target.value)}
            />
          </div>
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="supplier_id">Supplier</Label>
            <Select id="supplier_id" value={form.supplier_id} onChange={(e) => set("supplier_id", e.target.value)}>
              <option value="">No supplier</option>
              {suppliers?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </div>
        </div>

        {validationError && (
          <p role="alert" className="rounded-md bg-critical/5 px-3 py-2 text-sm text-critical">
            {validationError}
          </p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={mutation.isPending}>
            {isEdit ? "Save changes" : "Add product"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
