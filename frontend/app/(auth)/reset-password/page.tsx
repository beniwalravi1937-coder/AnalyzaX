"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import Image from "next/image";
import { useSearchParams, useRouter } from "next/navigation";
import { authApi } from "@/services/authApi";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tokenParam = searchParams.get("token") || "";

  const [token, setToken] = useState(tokenParam);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError("Password reset token is required.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await authApi.confirmPasswordReset(token, newPassword);
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: any) {
      setError(err.message || "Failed to reset password. The link may have expired.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-card">
      <div className="auth-header">
        <div className="auth-logo-wrap">
          <Image
            src="/logo.jpg"
            alt="AnalyzaX Logo"
            width={44}
            height={44}
            style={{ borderRadius: "8px", objectFit: "cover" }}
            priority
          />
        </div>
        <h1 className="auth-title">Set new password</h1>
        <p className="auth-subtitle">Choose a secure password for your AnalyzaX account</p>
      </div>

      {error && (
        <div className="auth-error-alert" role="alert">
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="auth-success-alert" role="status">
          <span>Password reset successful! Redirecting to sign in...</span>
        </div>
      )}

      {!success && (
        <form onSubmit={handleSubmit} className="auth-form">
          {!tokenParam && (
            <div className="auth-field">
              <label htmlFor="token" className="auth-label">
                Reset Token
              </label>
              <input
                id="token"
                type="text"
                required
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Paste token from email / link"
                className="auth-input"
                disabled={isLoading}
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="newPassword" className="auth-label">
              New Password (min. 8 characters)
            </label>
            <input
              id="newPassword"
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••••••"
              className="auth-input"
              disabled={isLoading}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="confirmPassword" className="auth-label">
              Confirm New Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••••••"
              className="auth-input"
              disabled={isLoading}
            />
          </div>

          <button type="submit" disabled={isLoading} className="btn btn-primary auth-submit-btn">
            {isLoading ? "Updating Password..." : "Reset Password"}
          </button>
        </form>
      )}

      <div className="auth-footer">
        <Link href="/login" className="auth-link">
          Return to sign in
        </Link>
      </div>

      <style jsx>{`
        .auth-card {
          width: 100%;
          max-width: 420px;
          background: rgba(15, 23, 42, 0.75);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          padding: 2.25rem 2rem;
          box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
        }
        .auth-header {
          text-align: center;
          margin-bottom: 1.75rem;
        }
        .auth-logo-wrap {
          display: inline-flex;
          margin-bottom: 0.75rem;
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
          border-radius: 8px;
        }
        .auth-title {
          font-size: 1.35rem;
          font-weight: 700;
          color: #f8fafc;
          margin: 0 0 0.35rem;
        }
        .auth-subtitle {
          font-size: 0.8125rem;
          color: var(--text-muted, #94a3b8);
          margin: 0;
        }
        .auth-error-alert {
          background: rgba(239, 68, 68, 0.12);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #fca5a5;
          padding: 0.75rem 0.875rem;
          border-radius: 8px;
          font-size: 0.8125rem;
          margin-bottom: 1.25rem;
        }
        .auth-success-alert {
          background: rgba(16, 185, 129, 0.12);
          border: 1px solid rgba(16, 185, 129, 0.3);
          color: #6ee7b7;
          padding: 0.75rem 0.875rem;
          border-radius: 8px;
          font-size: 0.8125rem;
          margin-bottom: 1.25rem;
        }
        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 1.125rem;
        }
        .auth-field {
          display: flex;
          flex-direction: column;
          gap: 0.375rem;
        }
        .auth-label {
          font-size: 0.8125rem;
          font-weight: 500;
          color: #cbd5e1;
        }
        .auth-input {
          width: 100%;
          background: rgba(2, 6, 23, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 8px;
          padding: 0.65rem 0.875rem;
          color: #f8fafc;
          font-size: 0.875rem;
        }
        .auth-input:focus {
          outline: none;
          border-color: var(--primary-color, #6366f1);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        .auth-submit-btn {
          width: 100%;
          padding: 0.7rem;
          font-weight: 600;
          font-size: 0.875rem;
          margin-top: 0.25rem;
          background: var(--primary-color, #6366f1);
          border: none;
          border-radius: 8px;
          color: #ffffff;
          cursor: pointer;
        }
        .auth-footer {
          margin-top: 1.5rem;
          text-align: center;
          font-size: 0.8125rem;
          color: var(--text-muted, #94a3b8);
        }
        .auth-link {
          color: var(--primary-color, #6366f1);
          text-decoration: none;
          font-weight: 500;
        }
        .auth-link:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="auth-container">
      <Suspense fallback={<div style={{ color: "#fff" }}>Loading reset form...</div>}>
        <ResetPasswordForm />
      </Suspense>
      <style jsx>{`
        .auth-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: radial-gradient(circle at top, #111827 0%, #030712 100%);
          padding: 1.5rem;
          color: var(--text-primary, #f8fafc);
        }
      `}</style>
    </div>
  );
}
