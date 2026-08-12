import { useCallback, useRef, useState, type ReactNode } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { uploadSalesCsv } from "@/api/sales";
import { QUERY_KEYS } from "@/lib/constants";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/api/client";
import type { CSVImportResult } from "@/types/api";

export function CsvUploadCard() {
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState<CSVImportResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const mutation = useMutation({
    mutationFn: (file: File) => uploadSalesCsv(file),
    onSuccess: (data) => {
      setResult(data);
      if (data.success) {
        queryClient.invalidateQueries({ queryKey: ["sales"] });
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
        toast({
          variant: "success",
          title: "CSV imported",
          description: `${data.imported_rows} of ${data.total_rows} rows imported.`,
        });
      } else {
        toast({
          variant: "error",
          title: "Unable to import the file",
          description: data.warnings[0]?.reason ?? "The file could not be processed.",
        });
      }
    },
    onError: (err) => {
      setResult(null);
      toast({
        variant: "error",
        title: "Upload failed",
        description: err instanceof ApiError ? err.message : "Please try again.",
      });
    },
  });

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith(".csv")) {
        toast({ variant: "error", title: "Invalid file type", description: "Please upload a .csv file." });
        return;
      }
      setResult(null);
      mutation.mutate(file);
    },
    [mutation, toast]
  );

  return (
    <Card>
      <CardContent className="p-5">
        <h3 className="mb-1 text-sm font-semibold text-foreground">Upload Historical Sales</h3>
        <p className="mb-4 text-sm text-muted-foreground">
          Accepted format: <code className="rounded bg-muted px-1 py-0.5 text-xs">date,product_id,quantity,price,promotion</code>
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            handleFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
          aria-label="Upload sales CSV file"
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
            isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
          }`}
        >
          <UploadCloud className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">
            {mutation.isPending ? "Uploading..." : "Drag & drop your CSV here, or click to browse"}
          </p>
          <p className="text-xs text-muted-foreground">Max file size 10MB</p>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>

        {result && (
          <div className="mt-4 space-y-3 rounded-md border border-border p-4">
            <div className="flex items-center gap-2">
              {result.success ? (
                <CheckCircle2 className="h-5 w-5 text-success" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-critical" />
              )}
              <p className="text-sm font-medium text-foreground">
                {result.success ? "Import complete" : "Import failed"}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <Stat label="Total rows" value={result.total_rows} icon={<FileText className="h-3.5 w-3.5" />} />
              <Stat label="Imported" value={result.imported_rows} tone="success" />
              <Stat label="Duplicates" value={result.duplicate_rows} tone="warning" />
              <Stat label="Invalid" value={result.invalid_rows} tone="critical" />
            </div>
            {result.warnings.length > 0 && (
              <div className="max-h-40 overflow-y-auto rounded-md bg-muted/50 p-3 text-xs">
                <p className="mb-1 font-medium text-foreground">Warnings</p>
                <ul className="space-y-1 text-muted-foreground">
                  {result.warnings.map((w, i) => (
                    <li key={i}>
                      Row {w.row}: {w.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          className="mt-4"
          onClick={() => inputRef.current?.click()}
          disabled={mutation.isPending}
        >
          Choose File
        </Button>
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  tone,
  icon,
}: {
  label: string;
  value: number;
  tone?: "success" | "warning" | "critical";
  icon?: ReactNode;
}) {
  const toneClass =
    tone === "success"
      ? "text-success"
      : tone === "warning"
        ? "text-warning"
        : tone === "critical"
          ? "text-critical"
          : "text-foreground";
  return (
    <div className="rounded-md bg-muted/50 px-3 py-2">
      <p className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-muted-foreground">
        {icon}
        {label}
      </p>
      <p className={`mt-0.5 text-lg font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}
