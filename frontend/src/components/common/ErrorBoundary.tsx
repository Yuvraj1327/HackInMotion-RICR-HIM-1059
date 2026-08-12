import { Component, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    // eslint-disable-next-line no-console
    console.error("Unexpected UI error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-6 text-center">
          <AlertTriangle className="h-10 w-10 text-critical" />
          <div>
            <p className="text-lg font-semibold text-foreground">Something went wrong</p>
            <p className="mt-1 text-sm text-muted-foreground">
              An unexpected error occurred. Try reloading the page.
            </p>
          </div>
          <Button onClick={() => window.location.reload()}>Reload StockPilot AI</Button>
        </div>
      );
    }
    return this.props.children;
  }
}
