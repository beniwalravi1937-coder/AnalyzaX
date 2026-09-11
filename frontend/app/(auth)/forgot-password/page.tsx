"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { authApi } from "@/services/authApi";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setDevToken(null);
    setIsLoading(true);

    try {
      const res = await authApi.requestPasswordReset(email);
      setMessage(res.message);
      if (res.dev_reset_token) {
        setDevToken(res.dev_reset_token);
      }
    } catch (err: any) {
      setError(err.message || "Failed to request password reset.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
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
          <h1 className="auth-title">Reset your password</h1>
          <p className="auth-subtitle">Enter your account email to generate a reset link</p>
        </div>

        {error && (
          <div className="auth-error-alert" role="alert">
            <span>{error}</span>
          </div>
        )}

        {message && (
          <div className="auth-success-alert" role="status">
            <span>{message}</span>
            {devToken && (
              <div style={{ marginTop: "0.75rem", fontSize: "0.75rem" }}>
                <strong>Dev Reset Token:</strong>{" "}
                <Link
                  href={`/reset-password?token=${devToken}`}
                  style={{ color: "#38bdf8", wordBreak: "break-all" }}
                >
                  Click here to complete password reset
                </Link>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label htmlFor="email" className="auth-label">
              Work Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="auth-input"
              disabled={isLoading}
            />
          </div>

          <button type="submit" disabled={isLoading} className="btn btn-primary auth-submit-btn">
            {isLoading ? "Generating Link..." : "Send Reset Link"}
          </button>
        </form>

        <div className="auth-footer">
          Remember your password?{" "}
          <Link href="/login" className="auth-link">
            Return to sign in
          </Link>
        </div>
      </div>

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
