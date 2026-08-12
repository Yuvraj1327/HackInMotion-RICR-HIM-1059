import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Rocket, CheckCircle2 } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Label } from "@/components/ui/Label";
import { Select } from "@/components/ui/Select";
import { seedDemoData } from "@/api/demo";
import { CATEGORIES, CATEGORY_LABELS, QUERY_KEYS, type DemoCategory } from "@/lib/constants";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { DemoSeedResponse } from "@/types/api";

const PROGRESS_STEPS = [
  "Generating products...",
  "Generating sales history...",
  "Preparing forecasting data...",
];

export function GenerateDemoDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [category, setCategory] = useState<DemoCategory>("grocery");
  const [days, setDays] = useState(120);
  const [numProducts, setNumProducts] = useState(20);
  const [stepIndex, setStepIndex] = useState(0);
  const [result, setResult] = useState<DemoSeedResponse | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const mutation = useMutation({
    mutationFn: async () => {
      setResult(null);
      setStepIndex(0);
      const stepTimer = setInterval(() => {
        setStepIndex((i) => Math.min(i + 1, PROGRESS_STEPS.length - 1));
      }, 900);
      try {
        const res = await seedDemoData({
          business_category: category,
          days_of_history: days,
          num_products: numProducts,
        });
        return res;
      } finally {
        clearInterval(stepTimer);
      }
    },
    onSuccess: (res) => {
      setResult(res);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.products });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.alerts });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.recommendations });
      queryClient.invalidateQueries({ queryKey: ["sales"] });
      toast({ variant: "success", title: "Demo store created", description: "Your data is ready to explore." });
    },
    onError: (err) => {
      toast({
        variant: "error",
        title: "Could not generate demo data",
        description: err instanceof ApiError ? err.message : "Please try again.",
      });
    },
  });

  function handleClose() {
    if (mutation.isPending) return;
    setResult(null);
    onClose();
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="🚀 Generate Demo Store"
      description="Create a realistic product catalog and sales history to explore StockPilot AI instantly."
    >
      {result ? (
        <div className="space-y-4">
          <div className="flex items-center gap-3 rounded-md bg-success/5 p-4">
            <CheckCircle2 className="h-6 w-6 shrink-0 text-success" />
            <div>
              <p className="font-medium text-foreground">Demo store created</p>
              <p className="text-sm text-muted-foreground">
                {result.products_created} products and {result.sales_records_created} sales records generated (
                {result.date_range_start} to {result.date_range_end}).
              </p>
            </div>
          </div>
          <Button className="w-full" onClick={handleClose}>
            Done
          </Button>
        </div>
      ) : mutation.isPending ? (
        <div className="flex flex-col items-center justify-center gap-3 py-8 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm font-medium text-foreground">{PROGRESS_STEPS[stepIndex]}</p>
          <p className="text-xs text-muted-foreground">This usually takes a few seconds.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="demo-category">Business category</Label>
            <Select
              id="demo-category"
              value={category}
              onChange={(e) => setCategory(e.target.value as DemoCategory)}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {CATEGORY_LABELS[c]}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="demo-days">History length</Label>
            <Select id="demo-days" value={days} onChange={(e) => setDays(Number(e.target.value))}>
              <option value={90}>90 days</option>
              <option value={120}>120 days</option>
              <option value={180}>180 days</option>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="demo-products">Number of products</Label>
            <Select
              id="demo-products"
              value={numProducts}
              onChange={(e) => setNumProducts(Number(e.target.value))}
            >
              <option value={15}>15</option>
              <option value={20}>20</option>
              <option value={25}>25</option>
            </Select>
          </div>
          <Button className="w-full" onClick={() => mutation.mutate()}>
            <Rocket className="h-4 w-4" />
            Generate Demo Store
          </Button>
        </div>
      )}
    </Modal>
  );
}
