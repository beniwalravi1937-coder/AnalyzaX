"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await register(email, password, displayName);
    } catch (err: any) {
      setError(err.message || "Failed to create account. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Branding Header */}
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
          <h1 className="auth-title">Create your AnalyzaX Account</h1>
          <p className="auth-subtitle">Get started with AI-driven enterprise data analytics</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="auth-error-alert" role="alert">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label htmlFor="displayName" className="auth-label">
              Full Name
            </label>
            <input
              id="displayName"
              type="text"
              required
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Alice Morgan"
              className="auth-input"
              disabled={isLoading}
            />
          </div>

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
              placeholder="alice@company.com"
              className="auth-input"
              disabled={isLoading}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="password" className="auth-label">
              Password (min. 8 characters)
            </label>
            <div className="password-input-wrapper">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="auth-input"
                disabled={isLoading}
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="confirmPassword" className="auth-label">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type={showPassword ? "text" : "password"}
              required
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••••••"
              className="auth-input"
              disabled={isLoading}
            />
          </div>

          <button type="submit" disabled={isLoading} className="btn btn-primary auth-submit-btn">
            {isLoading ? (
              <span className="auth-btn-spinner-wrap">
                <span className="auth-spinner" />
                Creating Account...
              </span>
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account?{" "}
          <Link href="/login" className="auth-link">
            Sign in
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
          max-width: 440px;
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
          letter-spacing: -0.02em;
        }
        .auth-subtitle {
          font-size: 0.8125rem;
          color: var(--text-muted, #94a3b8);
          margin: 0;
        }
        .auth-error-alert {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: rgba(239, 68, 68, 0.12);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #fca5a5;
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
        .password-input-wrapper {
          position: relative;
        }
        .auth-input {
          width: 100%;
          background: rgba(2, 6, 23, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 8px;
          padding: 0.65rem 0.875rem;
          color: #f8fafc;
          font-size: 0.875rem;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .auth-input:focus {
          outline: none;
          border-color: var(--primary-color, #6366f1);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        .password-toggle-btn {
          position: absolute;
          right: 0.75rem;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: var(--text-muted, #94a3b8);
          font-size: 0.75rem;
          cursor: pointer;
          font-weight: 500;
        }
        .password-toggle-btn:hover {
          color: #f8fafc;
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
          transition: background 0.15s;
        }
        .auth-submit-btn:hover:not(:disabled) {
          background: #4f46e5;
        }
        .auth-btn-spinner-wrap {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
        }
        .auth-spinner {
          width: 14px;
          height: 14px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
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
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
