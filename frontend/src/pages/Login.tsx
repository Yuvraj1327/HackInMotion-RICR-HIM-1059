import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { ApiError } from "@/api/client";
import { useToast } from "@/hooks/useToast";

export default function Login() {
  const { login, continueAsGuest } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGuestSubmitting, setIsGuestSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: Location })?.from?.pathname ?? "/dashboard";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to log in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGuest() {
    setError(null);
    setIsGuestSubmitting(true);
    try {
      const { seeded } = await continueAsGuest();
      if (!seeded) {
        toast({
          variant: "info",
          title: "Demo Mode started",
          description: "Sample data is taking a moment - use \"Generate Demo Store\" on the Dashboard if it doesn't appear.",
        });
      }
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to start Demo Mode. Please try again.");
    } finally {
      setIsGuestSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <Link to="/" aria-label="StockPilot AI home" className="mb-2">
            <img src="/assets/logo.png" alt="StockPilot AI — Inventory Intelligence" className="h-16 w-auto" />
          </Link>
          <p className="mt-1 text-sm text-muted-foreground">Predict demand. Prevent stockouts. Protect cash.</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-1 text-lg font-semibold text-foreground">Log in</h2>
          <p className="mb-5 text-sm text-muted-foreground">Welcome back. Enter your details to continue.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="owner@retailstore.com"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p role="alert" className="rounded-md bg-critical/5 px-3 py-2 text-sm text-critical">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full" isLoading={isSubmitting} disabled={isGuestSubmitting}>
              Log in
            </Button>
          </form>

          <div className="my-4 flex items-center gap-3" role="separator" aria-label="or">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs uppercase tracking-wide text-muted-foreground">or</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={handleGuest}
            isLoading={isGuestSubmitting}
            disabled={isSubmitting}
          >
            <Sparkles className="h-4 w-4" />
            Continue as Guest
          </Button>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Instantly enter Demo Mode with a sample store — no signup required. Perfect for judges and quick testing.
          </p>
        </div>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          Don't have an account?{" "}
          <Link to="/signup" className="font-medium text-primary hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}