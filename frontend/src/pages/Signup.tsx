import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { ApiError } from "@/api/client";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setIsSubmitting(true);
    try {
      await signup(email, password, businessName);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.code === "email_confirmation_required") {
        setInfo(err.message);
      } else {
        setError(err instanceof ApiError ? err.message : "Unable to create your account. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <Link
            to="/"
            aria-label="StockPilot AI home"
            className="mb-2 inline-flex items-center justify-center rounded-xl border border-border bg-white p-4 shadow-sm"
          >
            <img
              src="/assets/logo.png"
              alt="StockPilot AI — Inventory Intelligence"
              className="h-12 w-auto max-w-[220px] object-contain"
            />
          </Link>
          <p className="mt-1 text-sm text-muted-foreground">Predict demand. Prevent stockouts. Protect cash.</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-1 text-lg font-semibold text-foreground">Create your account</h2>
          <p className="mb-5 text-sm text-muted-foreground">Set up your business in under a minute.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="business_name">Business name</Label>
              <Input
                id="business_name"
                required
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="Sharma General Store"
              />
            </div>
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
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
              />
            </div>

            {error && (
              <p role="alert" className="rounded-md bg-critical/5 px-3 py-2 text-sm text-critical">
                {error}
              </p>
            )}
            {info && (
              <p role="status" className="rounded-md bg-primary/5 px-3 py-2 text-sm text-primary">
                {info}
              </p>
            )}

            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Create account
            </Button>
          </form>
        </div>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}