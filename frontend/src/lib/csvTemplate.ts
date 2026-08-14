import type { Product } from "@/types/api";

const TEMPLATE_DAYS = 7;

/**
 * Builds a ready-to-fill sales CSV using the user's OWN real product IDs
 * (no placeholder text). One row per product per day for the last
 * `TEMPLATE_DAYS` days, quantity left at 0 for the business owner to
 * type their real numbers over before re-uploading via the existing
 * "Upload Historical Sales" card - matches the exact accepted format
 * (date,product_id,quantity,price,promotion), so a filled-in copy of
 * this file uploads with zero "does not belong to this user" warnings.
 */
export function buildSalesCsvTemplate(products: Product[]): string {
  const today = new Date();
  const rows: string[] = ["date,product_id,quantity,price,promotion"];

  for (const product of products) {
    for (let i = TEMPLATE_DAYS - 1; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().slice(0, 10);
      rows.push(`${dateStr},${product.id},0,${product.price},0`);
    }
  }

  return rows.join("\n");
}

/** Triggers a browser download of `content` as a file named `filename`. */
export function downloadTextFile(filename: string, content: string, mimeType = "text/csv") {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}