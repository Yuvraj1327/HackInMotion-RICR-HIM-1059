import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@/hooks/useAuth";
import { ToastProvider } from "@/hooks/useToast";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";

/**
 * Single shared QueryClient. Sensible defaults for a dashboard-style app:
 * - staleTime keeps us from refetching on every component mount/focus,
 *   which matters here because several pages compute the same
 *   forecast/inventory data server-side (avoid hammering FastAPI).
 * - retry is capped and skips retrying both 4xx errors (they won't
 *   succeed on retry - a validation error stays a validation error) and
 *   network/timeout errors (a slow or unreachable backend won't get
 *   faster by retrying immediately - it just multiplies the wait, e.g.
 *   a 30s timeout retried twice means up to 90s of visible loading
 *   before the user ever sees an error). Failing fast on those lets the
 *   UI show a clear error + retry button instead of an indefinitely
 *   "stuck" skeleton.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        const status = error?.status;
        if (status && status >= 400 && status < 500) return false;
        if (error?.code === "network_error") return false;
        return failureCount < 2;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ToastProvider>
            <AuthProvider>{children}</AuthProvider>
          </ToastProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}



//provider.tsx