import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

/**
 * Purely presentational marker that the current session is a guest
 * ("Continue as Guest") session. Reuses the existing Badge primitive and
 * warning color token rather than introducing a new status color.
 */
export function DemoModeBadge({ className }: { className?: string }) {
  return (
    <Badge variant="warning" className={cn("uppercase tracking-wide", className)}>
      <Sparkles className="h-3 w-3" />
      Demo Mode
    </Badge>
  );
}