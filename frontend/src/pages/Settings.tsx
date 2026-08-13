////setting.tsx

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCcw, Truck, Plus, Trash2, Pencil } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Modal } from "@/components/ui/Modal";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { useAuth } from "@/hooks/useAuth";
import { listSuppliers, createSupplier, updateSupplier, deleteSupplier } from "@/api/suppliers";
import { resetDemoData } from "@/api/demo";
import { QUERY_KEYS } from "@/lib/constants";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { Supplier } from "@/types/api";

export default function Settings() {
  const { businessEmail, user } = useAuth();
  const [resetOpen, setResetOpen] = useState(false);
  const [supplierModalOpen, setSupplierModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [deletingSupplier, setDeletingSupplier] = useState<Supplier | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  const suppliersQuery = useQuery({ queryKey: QUERY_KEYS.suppliers, queryFn: listSuppliers });

  const resetMutation = useMutation({
    mutationFn: resetDemoData,
    onSuccess: () => {
      queryClient.invalidateQueries();
      toast({ variant: "success", title: "Data reset", description: "All products, suppliers, sales and alerts were cleared." });
      setResetOpen(false);
    },
    onError: (err) => {
      toast({ variant: "error", title: "Could not reset data", description: err instanceof ApiError ? err.message : undefined });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteSupplier(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.suppliers });
      toast({ variant: "success", title: "Supplier deleted" });
      setDeletingSupplier(null);
    },
    onError: (err) => {
      toast({ variant: "error", title: "Could not delete supplier", description: err instanceof ApiError ? err.message : undefined });
    },
  });

  return (
    <AppShell title="Settings">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 pt-0 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Email</span>
              <span className="font-medium text-foreground">{businessEmail}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">User ID</span>
              <span className="font-mono text-xs text-muted-foreground">{user?.id}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Truck className="h-4 w-4" /> Suppliers
            </CardTitle>
            <Button
              size="sm"
              onClick={() => {
                setEditingSupplier(null);
                setSupplierModalOpen(true);
              }}
            >
              <Plus className="h-4 w-4" /> Add Supplier
            </Button>
          </CardHeader>
          <CardContent className="pt-0">
            {suppliersQuery.isLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : !suppliersQuery.data || suppliersQuery.data.length === 0 ? (
              <EmptyState title="No suppliers yet" description="Add a supplier to track lead times and reliability." />
            ) : (
              <div className="divide-y divide-border">
                {suppliersQuery.data.map((s) => (
                  <div key={s.id} className="flex items-center justify-between py-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{s.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {s.contact_name ?? "—"} · Lead time {s.lead_time_days}d · Reliability{" "}
                        {Math.round(s.reliability_score * 100)}%
                      </p>
                    </div>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Edit ${s.name}`}
                        onClick={() => {
                          setEditingSupplier(s);
                          setSupplierModalOpen(true);
                        }}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" aria-label={`Delete ${s.name}`} onClick={() => setDeletingSupplier(s)}>
                        <Trash2 className="h-4 w-4 text-critical" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-critical/20">
          <CardHeader>
            <CardTitle className="text-base text-critical">Danger Zone</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="mb-3 text-sm text-muted-foreground">
              Permanently delete all products, suppliers, sales, forecasts, and alerts for this account. This is
              useful for resetting between demo runs.
            </p>
            <Button variant="destructive" onClick={() => setResetOpen(true)}>
              <RotateCcw className="h-4 w-4" /> Reset All Data
            </Button>
          </CardContent>
        </Card>
      </div>

      <SupplierFormModal
        open={supplierModalOpen}
        onClose={() => setSupplierModalOpen(false)}
        supplier={editingSupplier}
      />

      <ConfirmDialog
        open={!!deletingSupplier}
        onClose={() => setDeletingSupplier(null)}
        onConfirm={() => deletingSupplier && deleteMutation.mutate(deletingSupplier.id)}
        title="Delete supplier"
        description={`Are you sure you want to delete "${deletingSupplier?.name}"?`}
        isLoading={deleteMutation.isPending}
      />

      <ConfirmDialog
        open={resetOpen}
        onClose={() => setResetOpen(false)}
        onConfirm={() => resetMutation.mutate()}
        title="Reset all data?"
        description="This will permanently delete all your products, suppliers, sales, forecasts, and alerts. This cannot be undone."
        isLoading={resetMutation.isPending}
        confirmLabel="Reset Data"
      />
    </AppShell>
  );
}

function SupplierFormModal({
  open,
  onClose,
  supplier,
}: {
  open: boolean;
  onClose: () => void;
  supplier: Supplier | null;
}) {
  const isEdit = !!supplier;
  const [name, setName] = useState("");
  const [contactName, setContactName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [leadTime, setLeadTime] = useState("3");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  useEffect(() => {
    if (!open) return;
    setName(supplier?.name ?? "");
    setContactName(supplier?.contact_name ?? "");
    setEmail(supplier?.email ?? "");
    setPhone(supplier?.phone ?? "");
    setLeadTime(String(supplier?.lead_time_days ?? 3));
  }, [open, supplier]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        name,
        contact_name: contactName || null,
        email: email || null,
        phone: phone || null,
        lead_time_days: Number(leadTime),
      };
      return isEdit && supplier ? updateSupplier(supplier.id, payload) : createSupplier(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.suppliers });
      toast({ variant: "success", title: isEdit ? "Supplier updated" : "Supplier added" });
      onClose();
    },
    onError: (err) => {
      toast({ variant: "error", title: "Could not save supplier", description: err instanceof ApiError ? err.message : undefined });
    },
  });

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit Supplier" : "Add Supplier"}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="space-y-4"
      >
        <div className="space-y-1.5">
          <Label htmlFor="supplier-name">Name</Label>
          <Input id="supplier-name" required value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="supplier-contact">Contact name</Label>
          <Input id="supplier-contact" value={contactName} onChange={(e) => setContactName(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="supplier-email">Email</Label>
          <Input id="supplier-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="supplier-phone">Phone</Label>
          <Input id="supplier-phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="supplier-lead-time">Lead time (days)</Label>
          <Input
            id="supplier-lead-time"
            type="number"
            min={0}
            max={365}
            value={leadTime}
            onChange={(e) => setLeadTime(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={mutation.isPending}>
            {isEdit ? "Save changes" : "Add supplier"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
