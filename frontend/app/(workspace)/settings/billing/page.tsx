"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { SettingsNav } from "@/components/settings/SettingsNav";
import {
  getBillingOverview,
  getBillingPrices,
  createCheckoutSession,
  completeSandboxCheckout,
  changeSubscription,
  cancelSubscription,
  resumeSubscription,
  listInvoices,
  createPortalSession,
  reconcileBilling,
} from "@/services/billingApi";
import {
  BillingInterval,
  BillingOverviewResponse,
  BillingPrice,
  BillingReconciliationReport,
  Invoice,
  Subscription,
} from "@/types/billing";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  Clock,
  CreditCard,
  Download,
  ExternalLink,
  FileText,
  HelpCircle,
  Layers,
  RefreshCw,
  RotateCcw,
  Shield,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

export default function BillingStudioPage() {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<BillingOverviewResponse | null>(null);
  const [prices, setPrices] = useState<BillingPrice[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [billingInterval, setBillingInterval] = useState<BillingInterval>("month");
  
  // Modals & Action States
  const [isCheckoutModalOpen, setIsCheckoutModalOpen] = useState(false);
  const [selectedPlanForCheckout, setSelectedPlanForCheckout] = useState<string>("PRO");
  const [actionLoading, setActionLoading] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [reconciling, setReconciling] = useState(false);
  const [reconciliationReport, setReconciliationReport] = useState<BillingReconciliationReport | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [overviewData, pricesData, invoicesData] = await Promise.all([
        getBillingOverview(),
        getBillingPrices(),
        listInvoices(10, 0),
      ]);
      setOverview(overviewData);
      setPrices(pricesData);
      setInvoices(invoicesData.invoices);
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Failed to load billing information.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleInitiateCheckout = async (planCode: string) => {
    setSelectedPlanForCheckout(planCode);
    setIsCheckoutModalOpen(true);
  };

  const handleExecuteCheckout = async () => {
    try {
      setActionLoading(true);
      setNotification(null);

      // In sandbox mode, complete directly via the test helper for instant feedback
      const res = await completeSandboxCheckout(selectedPlanForCheckout, billingInterval);
      setNotification({
        type: "success",
        message: `Plan upgraded! ${res.message}`,
      });
      setIsCheckoutModalOpen(false);
      await loadData();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Checkout could not be completed.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelSubscription = async (cancelAtPeriodEnd: boolean) => {
    try {
      setActionLoading(true);
      setNotification(null);
      await cancelSubscription(cancelAtPeriodEnd, "User requested cancellation via Settings");
      setNotification({
        type: "info",
        message: cancelAtPeriodEnd
          ? "Your subscription has been scheduled for cancellation at the end of the billing cycle. Your data will remain safe."
          : "Your subscription has been immediately canceled. Your data remains safe.",
      });
      setIsCancelModalOpen(false);
      await loadData();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Failed to cancel subscription.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleResumeSubscription = async () => {
    try {
      setActionLoading(true);
      setNotification(null);
      await resumeSubscription();
      setNotification({
        type: "success",
        message: "Subscription successfully resumed! Auto-renewal is back on.",
      });
      await loadData();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Failed to resume subscription.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenPortal = async () => {
    try {
      setActionLoading(true);
      const res = await createPortalSession();
      window.location.href = res.portal_url;
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Customer billing portal unavailable.",
      });
      setActionLoading(false);
    }
  };

  const handleReconcile = async () => {
    try {
      setReconciling(true);
      const report = await reconcileBilling();
      setReconciliationReport(report);
      setNotification({
        type: report.is_healthy ? "success" : "info",
        message: report.is_healthy
          ? "Billing ledger reconciliation passed with 0 discrepancies."
          : `Reconciliation found ${report.mismatches_found} potential discrepancies.`,
      });
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Reconciliation failed.",
      });
    } finally {
      setReconciling(false);
    }
  };

  const currentPlan = overview?.plan_code || "FREE";
  const sub = overview?.subscription;

  // Find price for a tier and current interval
  const getPriceForTier = (tier: string) => {
    return prices.find(
      (p) => p.plan_code.toUpperCase() === tier.toUpperCase() && p.interval === billingInterval
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Navigation */}
        <SettingsNav />

        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-violet-600/10 border border-violet-500/20 text-violet-400">
                <CreditCard className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                  Billing & Subscriptions
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Phase 21 Verified
                  </span>
                </h1>
                <p className="text-slate-400 text-sm mt-1">
                  Manage commercial plan subscriptions, payments, billing intervals, and invoice receipts.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleReconcile}
              disabled={reconciling}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-colors shadow-sm"
              title="Audit internal subscriptions against provider state"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${reconciling ? "animate-spin" : ""}`} />
              {reconciling ? "Auditing..." : "Reconcile Ledger"}
            </button>

            <Link
              href="/settings/usage"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition-colors"
            >
              <Layers className="w-3.5 h-3.5 text-violet-400" />
              Usage Studio
            </Link>

            <button
              onClick={loadData}
              disabled={loading}
              className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Notifications */}
        {notification && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between text-sm ${
              notification.type === "success"
                ? "bg-emerald-950/40 border-emerald-500/30 text-emerald-300"
                : notification.type === "error"
                ? "bg-rose-950/40 border-rose-500/30 text-rose-300"
                : "bg-blue-950/40 border-blue-500/30 text-blue-300"
            }`}
          >
            <div className="flex items-center gap-2.5">
              {notification.type === "success" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : notification.type === "error" ? (
                <AlertCircle className="w-4 h-4 text-rose-400" />
              ) : (
                <Sparkles className="w-4 h-4 text-blue-400" />
              )}
              <span>{notification.message}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-slate-400 hover:text-slate-200 text-xs ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Scheduled Cancellation Warning Banner */}
        {sub?.cancel_at_period_end && (
          <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <div>
                <p className="font-semibold text-sm">Subscription cancellation scheduled</p>
                <p className="text-xs text-amber-300/80">
                  Your plan will remain active through {new Date(sub.current_period_end).toLocaleDateString()}.
                  Your datasets and assets are safe and will remain accessible in read-only mode after downgrade.
                </p>
              </div>
            </div>
            <button
              onClick={handleResumeSubscription}
              disabled={actionLoading}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-colors shadow-sm self-start md:self-auto"
            >
              Resume Subscription
            </button>
          </div>
        )}

        {/* Overview & Active Subscription Card */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Subscription Card */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800/80 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-violet-600/10 blur-[100px] rounded-full pointer-events-none" />

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
              <div>
                <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
                  Current Workspace Plan
                </span>
                <div className="flex items-center gap-3 mt-1">
                  <h2 className="text-3xl font-extrabold text-white tracking-tight">
                    {currentPlan}
                  </h2>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                      sub?.status === "active"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : sub?.status === "trialing"
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                        : sub?.status === "past_due"
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                        : "bg-slate-800 text-slate-400 border-slate-700"
                    }`}
                  >
                    {sub ? sub.status.toUpperCase() : "FREE TIER"}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {sub && (
                  <button
                    onClick={handleOpenPortal}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
                  >
                    <CreditCard className="w-3.5 h-3.5 text-slate-400" />
                    Billing Portal
                    <ExternalLink className="w-3 h-3 text-slate-400" />
                  </button>
                )}

                {sub && !sub.cancel_at_period_end && (
                  <button
                    onClick={() => setIsCancelModalOpen(true)}
                    className="px-3.5 py-2 rounded-xl text-xs font-medium text-rose-400 hover:bg-rose-950/30 border border-rose-900/50 transition-colors"
                  >
                    Cancel Plan
                  </button>
                )}
              </div>
            </div>

            {/* Subscription Metadata Details */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6">
              <div>
                <span className="text-xs text-slate-400 block">Billing Period</span>
                <span className="text-sm font-semibold text-slate-200 mt-0.5 block">
                  {sub ? (sub.plan_code.toLowerCase().includes("annual") ? "Annual" : "Monthly") : "N/A (Free)"}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Renewal / End Date</span>
                <span className="text-sm font-semibold text-slate-200 mt-0.5 block">
                  {sub ? new Date(sub.current_period_end).toLocaleDateString() : "Never"}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Payment Provider</span>
                <span className="text-sm font-semibold text-slate-200 mt-0.5 block capitalize">
                  {sub?.provider || "Internal"}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Customer ID</span>
                <span className="text-sm font-mono text-slate-300 mt-0.5 block truncate">
                  {overview?.customer?.external_customer_id || "None"}
                </span>
              </div>
            </div>
          </div>

          {/* Payment & Security Assurance Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-2.5 text-violet-400 font-semibold text-sm">
                <ShieldCheck className="w-5 h-5" />
                Security & Payment Guarantee
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                AnalyzaX never stores or handles raw payment cards, CVVs, or bank secrets.
                All transactions are encrypted and processed by PCI-DSS Level 1 certified gateways.
              </p>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                <div className="flex items-center gap-2 text-xs text-slate-300 font-medium">
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  Downgrade Safety Guarantee
                </div>
                <p className="text-[11px] text-slate-400">
                  Historical datasets, ML models, and analytics are never deleted upon plan cancellation or downgrade.
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/80 mt-4 flex items-center justify-between text-xs text-slate-400">
              <span>Billing Currency</span>
              <span className="font-semibold text-slate-200">USD ($)</span>
            </div>
          </div>
        </div>

        {/* Billing Interval Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4">
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">Available Plans & Pricing</h3>
            <p className="text-xs text-slate-400">Choose the optimal compute and storage tier for your team.</p>
          </div>

          <div className="inline-flex p-1 rounded-xl bg-slate-900 border border-slate-800">
            <button
              onClick={() => setBillingInterval("month")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                billingInterval === "month"
                  ? "bg-violet-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingInterval("year")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                billingInterval === "year"
                  ? "bg-violet-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Annual
              <span className="px-1.5 py-0.2 rounded text-[10px] font-extrabold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                SAVE 16%
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Tier Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* FREE TIER CARD */}
          <div
            className={`p-6 rounded-2xl border transition-all flex flex-col justify-between ${
              currentPlan === "FREE"
                ? "bg-slate-900/90 border-slate-700 shadow-lg ring-1 ring-slate-700"
                : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-bold text-white">Community</h4>
                {currentPlan === "FREE" && (
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                    Current Plan
                  </span>
                )}
              </div>
              <div className="mb-4">
                <span className="text-3xl font-extrabold text-white">$0</span>
                <span className="text-xs text-slate-400 ml-1">/ month</span>
              </div>
              <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                Essential data profiling, standard SQL analytics, and single-user exploratory workflows.
              </p>
              <ul className="space-y-2.5 text-xs text-slate-300">
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  1 GB Parquet storage limit
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  5 active projects
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  1 workspace seat
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  50 AI analyst questions / mo
                </li>
              </ul>
            </div>

            <div className="pt-6 border-t border-slate-800/80 mt-6">
              <button
                disabled
                className="w-full py-2.5 rounded-xl text-xs font-semibold bg-slate-800/60 text-slate-500 border border-slate-800 cursor-not-allowed"
              >
                Included
              </button>
            </div>
          </div>

          {/* PRO TIER CARD */}
          <div
            className={`p-6 rounded-2xl border transition-all flex flex-col justify-between relative ${
              currentPlan === "PRO"
                ? "bg-slate-900/90 border-violet-500/80 shadow-lg ring-1 ring-violet-500"
                : "bg-slate-900/40 border-slate-800/80 hover:border-violet-500/40"
            }`}
          >
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-[10px] font-extrabold tracking-wider uppercase bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md">
              Most Popular
            </div>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-bold text-white flex items-center gap-2">
                  Professional
                  <Sparkles className="w-4 h-4 text-violet-400" />
                </h4>
                {currentPlan === "PRO" && (
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-violet-500/20 text-violet-300 border border-violet-500/30">
                    Current Plan
                  </span>
                )}
              </div>
              <div className="mb-4">
                <span className="text-3xl font-extrabold text-white">
                  {billingInterval === "month" ? "$29" : "$290"}
                </span>
                <span className="text-xs text-slate-400 ml-1">
                  {billingInterval === "month" ? "/ month" : "/ year (save $58)"}
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                Full analytical machine learning, time-series forecasting, and higher throughput data pipelines.
              </p>
              <ul className="space-y-2.5 text-xs text-slate-300">
                <li className="flex items-center gap-2 font-medium text-white">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  10 GB Parquet storage limit
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  25 active projects
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  5 workspace team members
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  500 AI analyst inquiries / mo
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  100 ML models & 100 Forecast runs
                </li>
              </ul>
            </div>

            <div className="pt-6 border-t border-slate-800/80 mt-6">
              {currentPlan === "PRO" ? (
                <button
                  disabled
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-violet-600/20 text-violet-300 border border-violet-500/30 cursor-default"
                >
                  Active Plan
                </button>
              ) : (
                <button
                  onClick={() => handleInitiateCheckout("PRO")}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white transition-colors shadow-lg shadow-violet-600/20 flex items-center justify-center gap-1.5"
                >
                  Upgrade to Pro
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* TEAM TIER CARD */}
          <div
            className={`p-6 rounded-2xl border transition-all flex flex-col justify-between ${
              currentPlan === "TEAM"
                ? "bg-slate-900/90 border-blue-500 shadow-lg ring-1 ring-blue-500"
                : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-bold text-white">Team Collaboration</h4>
                {currentPlan === "TEAM" && (
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    Current Plan
                  </span>
                )}
              </div>
              <div className="mb-4">
                <span className="text-3xl font-extrabold text-white">
                  {billingInterval === "month" ? "$99" : "$990"}
                </span>
                <span className="text-xs text-slate-400 ml-1">
                  {billingInterval === "month" ? "/ month" : "/ year (save $198)"}
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                Expanded collaboration capacity, high-row SQL queries, and priority model execution.
              </p>
              <ul className="space-y-2.5 text-xs text-slate-300">
                <li className="flex items-center gap-2 font-medium text-white">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  50 GB Parquet storage limit
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  100 active projects
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  25 workspace team members
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  2,000 AI analyst inquiries / mo
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  500 ML models & 500 Forecast runs
                </li>
              </ul>
            </div>

            <div className="pt-6 border-t border-slate-800/80 mt-6">
              {currentPlan === "TEAM" ? (
                <button
                  disabled
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-blue-600/20 text-blue-300 border border-blue-500/30 cursor-default"
                >
                  Active Plan
                </button>
              ) : (
                <button
                  onClick={() => handleInitiateCheckout("TEAM")}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-colors border border-slate-700 flex items-center justify-center gap-1.5"
                >
                  Upgrade to Team
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Invoice & Payment History */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-400" />
                Invoice Receipts & Payment History
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Download verified tax invoices and review historical billing receipts.
              </p>
            </div>
          </div>

          {invoices.length === 0 ? (
            <div className="text-center py-10 border border-dashed border-slate-800/80 rounded-xl">
              <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400">No invoices generated for this workspace yet.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Invoice ID</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Receipt</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {invoices.map((inv) => (
                    <tr key={inv.invoice_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-slate-200">
                        {inv.external_invoice_id}
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {new Date(inv.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 font-semibold text-white">
                        {inv.total_display}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-medium uppercase ${
                            inv.status === "paid"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}
                        >
                          {inv.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {inv.hosted_invoice_url ? (
                          <a
                            href={inv.hosted_invoice_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors"
                          >
                            <Download className="w-3.5 h-3.5" />
                            View
                          </a>
                        ) : (
                          <span className="text-slate-600 text-xs">PDF</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Checkout Confirmation Modal */}
      {isCheckoutModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold text-white">Confirm Plan Upgrade</h3>
              <button
                onClick={() => setIsCheckoutModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Selected Tier</span>
                  <span className="font-bold text-white">{selectedPlanForCheckout}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Billing Interval</span>
                  <span className="font-bold text-white capitalize">{billingInterval}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Estimated Total</span>
                  <span className="font-bold text-emerald-400 text-sm">
                    {getPriceForTier(selectedPlanForCheckout)?.amount_display || "$29.00"}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-blue-950/30 border border-blue-500/20 text-blue-300 text-xs flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <span>Simulated deterministic checkout in development sandbox mode.</span>
              </div>
            </div>

            <div className="flex items-center gap-3 justify-end pt-2">
              <button
                onClick={() => setIsCheckoutModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteCheckout}
                disabled={actionLoading}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white transition-colors shadow-lg shadow-violet-600/20 flex items-center gap-2"
              >
                {actionLoading ? "Confirming..." : "Confirm Upgrade"}
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Subscription Modal */}
      {isCancelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex items-center gap-3 text-rose-400">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-lg font-bold text-white">Cancel Subscription</h3>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to cancel your workspace subscription?
              Your datasets, versions, models, and projects will <strong>never be deleted</strong>.
              You will continue to have full access through the end of your paid billing period.
            </p>

            <div className="flex items-center gap-3 justify-end pt-2">
              <button
                onClick={() => setIsCancelModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                Keep Subscription
              </button>
              <button
                onClick={() => handleCancelSubscription(true)}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white transition-colors shadow-lg shadow-rose-600/20"
              >
                {actionLoading ? "Processing..." : "Confirm Cancellation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
