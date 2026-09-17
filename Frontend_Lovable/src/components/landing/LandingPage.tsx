import React, { useState, useRef } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  ShieldCheck,
  Wand2,
  Brain,
  TrendingUp,
  ArrowRight,
  Sparkles,
  BarChart3,
  Database,
  CheckCircle2,
  Layers,
  ChevronRight,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Zap,
  Lock,
  LineChart,
  FileSpreadsheet,
} from "lucide-react";
import { AnalyzaXLogo } from "@/components/brand/AnalyzaXLogo";
import { DotField } from "./DotField";
import BorderGlow from "@/components/ui/BorderGlow";
import Lanyard from "@/components/Lanyard";

export function LandingPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"profiling" | "cleaning" | "analyst" | "forecasting">("profiling");
  const [isVideoMuted, setIsVideoMuted] = useState(true);
  const [isVideoPlaying, setIsVideoPlaying] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  const toggleVideoPlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsVideoPlaying(true);
    } else {
      videoRef.current.pause();
      setIsVideoPlaying(false);
    }
  };

  const toggleVideoMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !videoRef.current.muted;
    setIsVideoMuted(videoRef.current.muted);
  };

  const [isVideo2Muted, setIsVideo2Muted] = useState(true);
  const [isVideo2Playing, setIsVideo2Playing] = useState(true);
  const videoRef2 = useRef<HTMLVideoElement>(null);

  const toggleVideo2Play = () => {
    if (!videoRef2.current) return;
    if (videoRef2.current.paused) {
      videoRef2.current.play();
      setIsVideo2Playing(true);
    } else {
      videoRef2.current.pause();
      setIsVideo2Playing(false);
    }
  };

  const toggleVideo2Mute = () => {
    if (!videoRef2.current) return;
    videoRef2.current.muted = !videoRef2.current.muted;
    setIsVideo2Muted(videoRef2.current.muted);
  };

  return (
    <div
      className="landing-page"
      style={{
        minHeight: "100vh",
        backgroundColor: "#0b0f19",
        color: "#f8fafc",
        fontFamily: "var(--font-sans)",
        position: "relative",
        overflowX: "hidden",
      }}
    >
      {/* Background Interactive DotField */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "920px",
          pointerEvents: "none",
          zIndex: 0,
          overflow: "hidden",
          maskImage: "linear-gradient(to bottom, black 65%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(to bottom, black 65%, transparent 100%)",
        }}
        aria-hidden="true"
      >
        <DotField
          dotRadius={1.5}
          dotSpacing={14}
          bulgeStrength={67}
          glowRadius={160}
          sparkle={false}
          waveAmplitude={0}
          gradientFrom="rgba(168, 85, 247, 0.35)"
          gradientTo="rgba(180, 151, 207, 0.25)"
          glowColor="#120F17"
        />
      </div>

      {/* 1. Global Navigation Bar */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 60,
          backdropFilter: "blur(16px)",
          backgroundColor: "rgba(11, 15, 25, 0.8)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        <div
          style={{
            maxWidth: "1280px",
            margin: "0 auto",
            padding: "1rem 1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "2.5rem" }}>
            <Link to="/" style={{ display: "flex", alignItems: "center", textDecoration: "none" }}>
              <AnalyzaXLogo size={32} showText={true} />
            </Link>
            <nav style={{ display: "flex", alignItems: "center", gap: "1.75rem" }} className="md-show">
              <a href="#features" style={{ color: "#94a3b8", textDecoration: "none", fontSize: "0.875rem", fontWeight: 500, transition: "color 0.2s" }} onMouseOver={(e) => (e.currentTarget.style.color = "#f8fafc")} onMouseOut={(e) => (e.currentTarget.style.color = "#94a3b8")}>
                Features
              </a>
              <a href="#how-it-works" style={{ color: "#94a3b8", textDecoration: "none", fontSize: "0.875rem", fontWeight: 500, transition: "color 0.2s" }} onMouseOver={(e) => (e.currentTarget.style.color = "#f8fafc")} onMouseOut={(e) => (e.currentTarget.style.color = "#94a3b8")}>
                How It Works
              </a>
              <a href="#preview" style={{ color: "#94a3b8", textDecoration: "none", fontSize: "0.875rem", fontWeight: 500, transition: "color 0.2s" }} onMouseOver={(e) => (e.currentTarget.style.color = "#f8fafc")} onMouseOut={(e) => (e.currentTarget.style.color = "#94a3b8")}>
                Product Demo
              </a>
            </nav>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <Link
              to="/login"
              style={{
                color: "#cbd5e1",
                textDecoration: "none",
                fontSize: "0.875rem",
                fontWeight: 500,
                padding: "0.5rem 1rem",
                borderRadius: "8px",
                transition: "all 0.2s",
              }}
              onMouseOver={(e) => (e.currentTarget.style.color = "#ffffff")}
              onMouseOut={(e) => (e.currentTarget.style.color = "#cbd5e1")}
            >
              Sign in
            </Link>
            <Link
              to="/register"
              style={{
                background: "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)",
                color: "#ffffff",
                textDecoration: "none",
                fontSize: "0.875rem",
                fontWeight: 600,
                padding: "0.55rem 1.25rem",
                borderRadius: "8px",
                boxShadow: "0 0 20px rgba(99, 102, 241, 0.4)",
                transition: "all 0.2s",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.boxShadow = "0 0 30px rgba(168, 85, 247, 0.6)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.boxShadow = "0 0 20px rgba(99, 102, 241, 0.4)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              Create an account
              <ArrowRight style={{ width: "16px", height: "16px" }} />
            </Link>
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section
        style={{
          position: "relative",
          padding: "5.5rem 1.5rem 4rem",
          overflow: "visible",
          textAlign: "center",
          maxWidth: "1240px",
          margin: "0 auto",
        }}
      >
        {/* Interactive 3D Draggable Lanyard Card at top-right corner */}
        <div className="lanyard-hero-anchor" aria-label="AnalyzaX Interactive 3D Lanyard Pass">
          <Lanyard
            position={[0, 0, 24]}
            anchorX={1.1}
            gravity={[0, -40, 0]}
            frontImage="/lanyard-card-front.png"
            backImage="/lanyard-card-back.png"
            imageFit="cover"
            lanyardWidth={1.1}
          />
        </div>
        {/* Glow backdrop effects */}
        <div
          style={{
            position: "absolute",
            top: "-150px",
            left: "50%",
            transform: "translateX(-50%)",
            width: "650px",
            height: "450px",
            background: "radial-gradient(circle, rgba(99, 102, 241, 0.22) 0%, rgba(168, 85, 247, 0.08) 50%, transparent 70%)",
            pointerEvents: "none",
            filter: "blur(60px)",
            zIndex: 0,
          }}
        />

        <div style={{ position: "relative", zIndex: 1 }}>
          {/* Pill Badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.6rem",
              padding: "0.35rem 1rem",
              borderRadius: "9999px",
              backgroundColor: "rgba(99, 102, 241, 0.12)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              fontSize: "0.8125rem",
              fontWeight: 500,
              color: "#a5b4fc",
              marginBottom: "1.75rem",
            }}
          >
            <Sparkles style={{ width: "14px", height: "14px", color: "#818cf8" }} />
            <span>Next-Generation Intelligent Data Workspace</span>
            <span style={{ backgroundColor: "rgba(99, 102, 241, 0.25)", padding: "0.1rem 0.45rem", borderRadius: "9999px", fontSize: "0.6875rem", fontWeight: 700 }}>
              NEW
            </span>
          </div>

          {/* Benefit-Driven Headline */}
          <h1
            style={{
              fontSize: "clamp(2.5rem, 5.5vw, 4.25rem)",
              fontWeight: 800,
              letterSpacing: "-0.035em",
              lineHeight: 1.12,
              marginBottom: "1.5rem",
              maxWidth: "920px",
              margin: "0 auto 1.5rem",
            }}
          >
            Turn Raw Spreadsheets Into{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #38bdf8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Executive Insights
            </span>{" "}
            in Seconds
          </h1>

          {/* Subheadline */}
          <p
            style={{
              fontSize: "clamp(1.05rem, 2vw, 1.25rem)",
              color: "#94a3b8",
              maxWidth: "740px",
              margin: "0 auto 2.5rem",
              lineHeight: 1.6,
              fontWeight: 400,
            }}
          >
            AnalyzaX automatically audits your data quality, fixes inconsistencies, and reveals the key drivers behind your business metrics — with a built-in AI analyst that answers questions in plain language.
          </p>

          {/* Main Action CTAs */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "1.25rem",
              flexWrap: "wrap",
              marginBottom: "3rem",
            }}
          >
            <Link
              to="/register"
              style={{
                background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                color: "#ffffff",
                textDecoration: "none",
                fontSize: "1.0625rem",
                fontWeight: 600,
                padding: "0.85rem 2rem",
                borderRadius: "10px",
                boxShadow: "0 10px 30px rgba(99, 102, 241, 0.45)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.6rem",
                transition: "all 0.2s ease-in-out",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "0 15px 40px rgba(99, 102, 241, 0.6)";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 10px 30px rgba(99, 102, 241, 0.45)";
              }}
            >
              Create Free Account
              <ArrowRight style={{ width: "18px", height: "18px" }} />
            </Link>

            <Link
              to="/login"
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.05)",
                color: "#e2e8f0",
                textDecoration: "none",
                fontSize: "1.0625rem",
                fontWeight: 500,
                padding: "0.85rem 1.85rem",
                borderRadius: "10px",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                transition: "all 0.2s",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.09)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.25)";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.12)";
              }}
            >
              Sign In to Workspace
            </Link>
          </div>

          {/* Social Proof & Trust Badges */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "2rem",
              flexWrap: "wrap",
              fontSize: "0.8125rem",
              color: "#64748b",
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <CheckCircle2 style={{ width: "15px", height: "15px", color: "#10b981" }} />
              No credit card required
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <FileSpreadsheet style={{ width: "15px", height: "15px", color: "#6366f1" }} />
              Supports CSV, Excel & Parquet
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Lock style={{ width: "15px", height: "15px", color: "#38bdf8" }} />
              Private & encrypted in browser
            </span>
          </div>
        </div>
      </section>

      {/* 3. Product Preview Showcase (Interactive Dark-Mode Mockup) */}
      <section id="preview" style={{ padding: "1rem 1.5rem 5rem", maxWidth: "1240px", margin: "0 auto" }}>
        <div
          style={{
            borderRadius: "16px",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            background: "linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.95) 100%)",
            boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 40px rgba(99, 102, 241, 0.15)",
            overflow: "hidden",
          }}
        >
          {/* Mockup Window Header */}
          <div
            style={{
              padding: "0.85rem 1.25rem",
              borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              backgroundColor: "rgba(15, 23, 42, 0.6)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#ef4444" }} />
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#f59e0b" }} />
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#10b981" }} />
              <span style={{ marginLeft: "0.75rem", fontSize: "0.75rem", color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                analyzax.workspace / student_exam_performance.csv
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <span style={{ fontSize: "0.6875rem", backgroundColor: "rgba(16, 185, 129, 0.15)", color: "#10b981", border: "1px solid rgba(16, 185, 129, 0.3)", padding: "0.15rem 0.5rem", borderRadius: "4px", fontWeight: 600 }}>
                ● 100,000 ROWS AUDITED
              </span>
              <span style={{ fontSize: "0.6875rem", backgroundColor: "rgba(99, 102, 241, 0.15)", color: "#a5b4fc", border: "1px solid rgba(99, 102, 241, 0.3)", padding: "0.15rem 0.5rem", borderRadius: "4px", fontWeight: 600 }}>
                44 ATTRIBUTES
              </span>
            </div>
          </div>

          {/* Mockup Workbench Body */}
          <div style={{ padding: "1.75rem" }}>
            {/* Top KPI Cards */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "1rem",
                marginBottom: "1.5rem",
              }}
            >
              <div style={{ padding: "1.25rem", borderRadius: "10px", backgroundColor: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "0.35rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Dataset Health Score
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
                  <span style={{ fontSize: "1.75rem", fontWeight: 700, color: "#10b981" }}>95.5%</span>
                  <span style={{ fontSize: "0.8125rem", color: "#10b981", fontWeight: 600 }}>Grade A</span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.35rem" }}>Clean structure ready for modelling</div>
              </div>

              <div style={{ padding: "1.25rem", borderRadius: "10px", backgroundColor: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "0.35rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Primary Outcome Target
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
                  <span style={{ fontSize: "1.75rem", fontWeight: 700, color: "#818cf8" }}>exam_score</span>
                  <span style={{ fontSize: "0.75rem", backgroundColor: "rgba(99, 102, 241, 0.2)", color: "#c7d2fe", padding: "0.1rem 0.4rem", borderRadius: "4px" }}>
                    Regression
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.35rem" }}>Auto-detected with 94% confidence</div>
              </div>

              <div style={{ padding: "1.25rem", borderRadius: "10px", backgroundColor: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "0.35rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Top Predictor Identified
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
                  <span style={{ fontSize: "1.75rem", fontWeight: 700, color: "#38bdf8" }}>study_hours</span>
                  <span style={{ fontSize: "0.8125rem", color: "#38bdf8", fontWeight: 600 }}>r = +0.64</span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.35rem" }}>Strongest positive impact on scores</div>
              </div>

              <div style={{ padding: "1.25rem", borderRadius: "10px", backgroundColor: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "0.35rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Prediction Model Accuracy
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
                  <span style={{ fontSize: "1.75rem", fontWeight: 700, color: "#c084fc" }}>0.91 R²</span>
                  <span style={{ fontSize: "0.8125rem", color: "#c084fc", fontWeight: 600 }}>RMSE 3.42</span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.35rem" }}>Trained automatically across 100k rows</div>
              </div>
            </div>

            {/* Simulated AI Analyst Insight Card */}
            <div
              style={{
                borderRadius: "10px",
                backgroundColor: "rgba(99, 102, 241, 0.08)",
                border: "1px solid rgba(99, 102, 241, 0.25)",
                padding: "1.25rem 1.5rem",
                display: "flex",
                gap: "1rem",
                alignItems: "flex-start",
              }}
            >
              <div style={{ padding: "0.5rem", borderRadius: "8px", backgroundColor: "rgba(99, 102, 241, 0.2)", color: "#a5b4fc" }}>
                <Brain style={{ width: "20px", height: "20px" }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "#f8fafc" }}>
                    AI Analyst Executive Brief
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "#818cf8", fontFamily: "var(--font-mono)" }}>
                    Automated Analysis
                  </span>
                </div>
                <p style={{ fontSize: "0.84rem", color: "#cbd5e1", lineHeight: 1.55, margin: 0 }}>
                  “Students studying <strong style={{ color: "#ffffff" }}>&gt;4 hours daily</strong> paired with regular practice tests achieve a <strong style={{ color: "#10b981" }}>92.4% pass rate</strong>, compared to 54.1% for irregular study habits. Exam anxiety exhibits an inverse threshold at level 7, after which scores degrade by an average of 14.8 points.”
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Four Core Feature Highlights (Benefit-Driven) */}
      <section id="features" style={{ padding: "5rem 1.5rem", maxWidth: "1240px", margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: "4rem" }}>
          <h2 style={{ fontSize: "clamp(2rem, 3.5vw, 2.75rem)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: "1rem" }}>
            Everything You Need to Understand Your Data
          </h2>
          <p style={{ fontSize: "1.125rem", color: "#94a3b8", maxWidth: "680px", margin: "0 auto", lineHeight: 1.6 }}>
            Replace fragmented tools, complex Python scripts, and manual spreadsheet calculations with a unified, intelligent analytical engine.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1.75rem",
          }}
        >
          {/* Pillar 1: Automated Data Profiling */}
          <BorderGlow
            borderRadius={14}
            glowRadius={36}
            glowIntensity={1.0}
            edgeSensitivity={30}
            backgroundColor="rgba(14, 19, 38, 0.75)"
            colors={['#10b981', '#34d399', '#38bdf8']}
            style={{ padding: "2rem" }}
          >
            <div style={{ width: "44px", height: "44px", borderRadius: "10px", backgroundColor: "rgba(16, 185, 129, 0.12)", color: "#10b981", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.25rem" }}>
              <ShieldCheck style={{ width: "24px", height: "24px" }} />
            </div>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "0.6rem" }}>
              Instant Data Health Audit
            </h3>
            <p style={{ fontSize: "0.9rem", color: "#94a3b8", lineHeight: 1.6, marginBottom: "1rem" }}>
              Get a complete structural report the moment you drop in a file. Instantly spot missing records, outliers, and data type inconsistencies before you make business decisions.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.84rem", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#10b981" }} />
                Automated 0-100% data quality score
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#10b981" }} />
                Instant distribution histograms per column
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#10b981" }} />
                Automatic target & outcome detection
              </li>
            </ul>
          </BorderGlow>

          {/* Pillar 2: Intelligent Data Cleaning */}
          <BorderGlow
            borderRadius={14}
            glowRadius={36}
            glowIntensity={1.0}
            edgeSensitivity={30}
            backgroundColor="rgba(14, 19, 38, 0.75)"
            colors={['#c084fc', '#f472b6', '#a855f7']}
            style={{ padding: "2rem" }}
          >
            <div style={{ width: "44px", height: "44px", borderRadius: "10px", backgroundColor: "rgba(168, 85, 247, 0.12)", color: "#c084fc", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.25rem" }}>
              <Wand2 style={{ width: "24px", height: "24px" }} />
            </div>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "0.6rem" }}>
              One-Click Smart Cleaning
            </h3>
            <p style={{ fontSize: "0.9rem", color: "#94a3b8", lineHeight: 1.6, marginBottom: "1rem" }}>
              Eliminate hours of manual spreadsheet cleanup. Remove duplicate records, fill missing values intelligently, and track every version with complete audit lineage.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.84rem", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#c084fc" }} />
                Smart deduplication and normalization
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#c084fc" }} />
                Statistical missing-value imputation
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#c084fc" }} />
                Full audit history & version branching
              </li>
            </ul>
          </BorderGlow>

          {/* Pillar 3: AI Analyst */}
          <BorderGlow
            borderRadius={14}
            glowRadius={36}
            glowIntensity={1.0}
            edgeSensitivity={30}
            backgroundColor="rgba(14, 19, 38, 0.75)"
            colors={['#818cf8', '#a78bfa', '#6366f1']}
            style={{ padding: "2rem" }}
          >
            <div style={{ width: "44px", height: "44px", borderRadius: "10px", backgroundColor: "rgba(99, 102, 241, 0.12)", color: "#818cf8", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.25rem" }}>
              <Brain style={{ width: "24px", height: "24px" }} />
            </div>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "0.6rem" }}>
              Conversational AI Analyst
            </h3>
            <p style={{ fontSize: "0.9rem", color: "#94a3b8", lineHeight: 1.6, marginBottom: "1rem" }}>
              Ask questions in plain English and receive instant answers, interactive charts, and business takeaways without having to write SQL or formulas.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.84rem", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#818cf8" }} />
                Natural language to answers & charts
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#818cf8" }} />
                Automated driver & anomaly detection
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#818cf8" }} />
                Board-ready executive summaries
              </li>
            </ul>
          </BorderGlow>

          {/* Pillar 4: Forecasting & Predictive Modeling */}
          <BorderGlow
            borderRadius={14}
            glowRadius={36}
            glowIntensity={1.0}
            edgeSensitivity={30}
            backgroundColor="rgba(14, 19, 38, 0.75)"
            colors={['#38bdf8', '#60a5fa', '#818cf8']}
            style={{ padding: "2rem" }}
          >
            <div style={{ width: "44px", height: "44px", borderRadius: "10px", backgroundColor: "rgba(56, 189, 248, 0.12)", color: "#38bdf8", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.25rem" }}>
              <TrendingUp style={{ width: "24px", height: "24px" }} />
            </div>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "0.6rem" }}>
              No-Code Predictive Modeling
            </h3>
            <p style={{ fontSize: "0.9rem", color: "#94a3b8", lineHeight: 1.6, marginBottom: "1rem" }}>
              Predict future trends and outcomes with automated machine learning. Train regression and classification models in one click with clear accuracy metrics.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.84rem", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#38bdf8" }} />
                Automated model selection & training
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#38bdf8" }} />
                Feature importance and impact rankings
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <CheckCircle2 style={{ width: "14px", height: "14px", color: "#38bdf8" }} />
                Confidence intervals & scenario simulations
              </li>
            </ul>
          </BorderGlow>
        </div>
      </section>

      {/* 4.25. Source Lineage & Citation Intelligence Section (promo2.mp4) */}
      <section
        id="sources-citations"
        style={{
          padding: "5rem 1.5rem 4rem",
          maxWidth: "1240px",
          margin: "0 auto",
          position: "relative",
          overflow: "visible",
        }}
      >
        {/* Ambient Radial Glow */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "55%",
            transform: "translate(-50%, -50%)",
            width: "75%",
            maxWidth: "850px",
            height: "420px",
            background: "radial-gradient(ellipse at center, rgba(168, 85, 247, 0.14) 0%, rgba(99, 102, 241, 0.08) 50%, transparent 70%)",
            pointerEvents: "none",
            filter: "blur(65px)",
            zIndex: 0,
          }}
          aria-hidden="true"
        />

        <div
          style={{
            position: "relative",
            zIndex: 1,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "3.5rem",
            alignItems: "center",
          }}
        >
          {/* Left Column: Content Narrative (matching reference photo) */}
          <div style={{ maxWidth: "540px" }}>
            {/* Asterisk / Starburst Symbol from Reference Image */}
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "12px",
                backgroundColor: "rgba(168, 85, 247, 0.12)",
                border: "1px solid rgba(168, 85, 247, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#c084fc",
                marginBottom: "1.5rem",
                boxShadow: "0 0 25px rgba(168, 85, 247, 0.2)",
              }}
              aria-hidden="true"
            >
              <svg
                width="26"
                height="26"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.75"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="12" y1="2" x2="12" y2="22" />
                <line x1="2" y1="12" x2="22" y2="12" />
                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                <line x1="19.07" y1="4.93" x2="4.93" y2="19.07" />
              </svg>
            </div>

            {/* Pill Badge */}
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.3rem 0.85rem",
                borderRadius: "9999px",
                backgroundColor: "rgba(99, 102, 241, 0.12)",
                border: "1px solid rgba(99, 102, 241, 0.3)",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "#a5b4fc",
                marginBottom: "1.25rem",
                letterSpacing: "0.03em",
                textTransform: "uppercase",
              }}
            >
              <Sparkles style={{ width: "13px", height: "13px", color: "#818cf8" }} />
              <span>Verifiable Citations</span>
            </div>

            {/* Headline matching the reference image theme */}
            <h2
              style={{
                fontSize: "clamp(2.1rem, 3.8vw, 3rem)",
                fontWeight: 800,
                letterSpacing: "-0.03em",
                lineHeight: 1.15,
                marginBottom: "1.25rem",
                color: "#ffffff",
              }}
            >
              See the{" "}
              <span
                style={{
                  background: "linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #38bdf8 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                source
              </span>
              , not just the answer
            </h2>

            {/* Subtitle / Paragraph */}
            <p
              style={{
                fontSize: "1.0625rem",
                color: "#94a3b8",
                lineHeight: 1.65,
                marginBottom: "2rem",
              }}
            >
              Gain confidence in every response because AnalyzaX provides clear citations for its work, showing you the exact rows, formulas, and data lineage behind every generated insight.
            </p>

            {/* Trust & Lineage Highlight Points */}
            <div style={{ display: "flex", flexDirection: "column", gap: "0.9rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.75rem",
                  padding: "0.85rem 1rem",
                  borderRadius: "10px",
                  backgroundColor: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid rgba(255, 255, 255, 0.07)",
                }}
              >
                <div style={{ marginTop: "2px", color: "#10b981" }}>
                  <CheckCircle2 style={{ width: "16px", height: "16px" }} />
                </div>
                <div>
                  <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#f1f5f9" }}>
                    Row-Level Citations & Audit Lineage
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "2px", lineHeight: 1.5 }}>
                    Inspect the exact dataset rows and columns that produced each chart and AI summary.
                  </div>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.75rem",
                  padding: "0.85rem 1rem",
                  borderRadius: "10px",
                  backgroundColor: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid rgba(255, 255, 255, 0.07)",
                }}
              >
                <div style={{ marginTop: "2px", color: "#38bdf8" }}>
                  <CheckCircle2 style={{ width: "16px", height: "16px" }} />
                </div>
                <div>
                  <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#f1f5f9" }}>
                    Deterministic Mathematical Engine
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "2px", lineHeight: 1.5 }}>
                    Zero numerical hallucinations. All quantiles, metrics, and correlations are computed with DuckDB & Polars.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Video Player Mockup Window (promo2.mp4) */}
          <div
            style={{
              position: "relative",
              borderRadius: "18px",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              background: "linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%)",
              boxShadow: "0 25px 70px -15px rgba(0, 0, 0, 0.8), 0 0 50px rgba(168, 85, 247, 0.16)",
              overflow: "hidden",
              transition: "all 0.3s ease",
            }}
          >
            {/* Mac-style Window Titlebar */}
            <div
              style={{
                padding: "0.75rem 1.25rem",
                borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                backgroundColor: "rgba(15, 23, 42, 0.7)",
                backdropFilter: "blur(12px)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#ef4444" }} />
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#f59e0b" }} />
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#10b981" }} />
                <span style={{ marginLeft: "0.75rem", fontSize: "0.75rem", color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                  analyzax.citations / source_evidence.mp4
                </span>
              </div>

              {/* Video 2 Controls: Play/Pause & Sound */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <button
                  type="button"
                  onClick={toggleVideo2Play}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.35rem",
                    fontSize: "0.75rem",
                    padding: "0.25rem 0.6rem",
                    borderRadius: "6px",
                    backgroundColor: "rgba(255, 255, 255, 0.06)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    color: "#cbd5e1",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.12)")}
                  onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)")}
                  aria-label={isVideo2Playing ? "Pause citations video" : "Play citations video"}
                >
                  {isVideo2Playing ? (
                    <>
                      <Pause style={{ width: "11px", height: "11px", color: "#c084fc" }} />
                      <span>Pause</span>
                    </>
                  ) : (
                    <>
                      <Play style={{ width: "11px", height: "11px", color: "#c084fc" }} />
                      <span>Play</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={toggleVideo2Mute}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.35rem",
                    fontSize: "0.75rem",
                    padding: "0.25rem 0.6rem",
                    borderRadius: "6px",
                    backgroundColor: isVideo2Muted ? "rgba(255, 255, 255, 0.06)" : "rgba(168, 85, 247, 0.2)",
                    border: isVideo2Muted ? "1px solid rgba(255, 255, 255, 0.12)" : "1px solid rgba(168, 85, 247, 0.4)",
                    color: isVideo2Muted ? "#cbd5e1" : "#c084fc",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.15)")}
                  onMouseOut={(e) => (e.currentTarget.style.backgroundColor = isVideo2Muted ? "rgba(255, 255, 255, 0.06)" : "rgba(168, 85, 247, 0.2)")}
                  aria-label={isVideo2Muted ? "Unmute audio" : "Mute audio"}
                >
                  {isVideo2Muted ? (
                    <>
                      <VolumeX style={{ width: "11px", height: "11px" }} />
                      <span>Unmute</span>
                    </>
                  ) : (
                    <>
                      <Volume2 style={{ width: "11px", height: "11px" }} />
                      <span>Sound On</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Video 2 Player Display */}
            <div style={{ position: "relative", backgroundColor: "#060913", overflow: "hidden" }}>
              <video
                ref={videoRef2}
                src="/promo2.mp4"
                autoPlay
                muted
                loop
                playsInline
                preload="metadata"
                style={{
                  width: "100%",
                  height: "auto",
                  maxHeight: "520px",
                  display: "block",
                  objectFit: "contain",
                  margin: "0 auto",
                  borderRadius: "0 0 18px 18px",
                }}
                onPlay={() => setIsVideo2Playing(true)}
                onPause={() => setIsVideo2Playing(false)}
              />
            </div>
          </div>
        </div>
      </section>

      {/* 4.5. Advertising Video Showcase Section (Directly Above "How AnalyzaX Works") */}
      <section
        id="video-showcase"
        style={{
          padding: "4.5rem 1.5rem 5rem",
          maxWidth: "1240px",
          margin: "0 auto",
          position: "relative",
          overflow: "visible",
        }}
      >
        {/* Ambient Radial Glow */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "80%",
            maxWidth: "900px",
            height: "450px",
            background: "radial-gradient(ellipse at center, rgba(99, 102, 241, 0.16) 0%, rgba(168, 85, 247, 0.08) 45%, transparent 70%)",
            pointerEvents: "none",
            filter: "blur(60px)",
            zIndex: 0,
          }}
          aria-hidden="true"
        />

        {/* Section Header */}
        <div style={{ textAlign: "center", marginBottom: "3rem", position: "relative", zIndex: 1 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.35rem 0.95rem",
              borderRadius: "9999px",
              backgroundColor: "rgba(99, 102, 241, 0.12)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              fontSize: "0.8125rem",
              fontWeight: 500,
              color: "#a5b4fc",
              marginBottom: "1.25rem",
            }}
          >
            <Sparkles style={{ width: "14px", height: "14px", color: "#818cf8" }} />
            <span>Product Showcase</span>
            <span style={{ backgroundColor: "rgba(99, 102, 241, 0.25)", padding: "0.1rem 0.45rem", borderRadius: "9999px", fontSize: "0.6875rem", fontWeight: 700 }}>
              10s DEMO
            </span>
          </div>
          <h2
            style={{
              fontSize: "clamp(2rem, 3.5vw, 2.75rem)",
              fontWeight: 700,
              letterSpacing: "-0.03em",
              marginBottom: "1rem",
            }}
          >
            See AnalyzaX in Action
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "#94a3b8",
              maxWidth: "680px",
              margin: "0 auto",
              lineHeight: 1.6,
            }}
          >
            Watch how effortlessly raw, complex datasets transform into automated audits, visual charts, and actionable executive insights.
          </p>
        </div>

        {/* Video Player Mockup Window */}
        <div
          style={{
            position: "relative",
            zIndex: 1,
            maxWidth: "1060px",
            margin: "0 auto",
            borderRadius: "18px",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            background: "linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%)",
            boxShadow: "0 25px 70px -15px rgba(0, 0, 0, 0.8), 0 0 50px rgba(99, 102, 241, 0.16)",
            overflow: "hidden",
            transition: "all 0.3s ease",
          }}
        >
          {/* Mac-style Window Titlebar */}
          <div
            style={{
              padding: "0.85rem 1.25rem",
              borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              backgroundColor: "rgba(15, 23, 42, 0.7)",
              backdropFilter: "blur(12px)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#ef4444" }} />
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#f59e0b" }} />
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#10b981" }} />
              <span style={{ marginLeft: "0.75rem", fontSize: "0.75rem", color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                analyzax_product_demo.mp4
              </span>
            </div>

            {/* Top Quick Actions: Play/Pause & Audio Mute/Unmute */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <button
                type="button"
                onClick={toggleVideoPlay}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  fontSize: "0.75rem",
                  padding: "0.25rem 0.65rem",
                  borderRadius: "6px",
                  backgroundColor: "rgba(255, 255, 255, 0.06)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  color: "#cbd5e1",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.12)")}
                onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)")}
                aria-label={isVideoPlaying ? "Pause video" : "Play video"}
              >
                {isVideoPlaying ? (
                  <>
                    <Pause style={{ width: "12px", height: "12px", color: "#818cf8" }} />
                    <span>Pause</span>
                  </>
                ) : (
                  <>
                    <Play style={{ width: "12px", height: "12px", color: "#818cf8" }} />
                    <span>Play</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={toggleVideoMute}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  fontSize: "0.75rem",
                  padding: "0.25rem 0.65rem",
                  borderRadius: "6px",
                  backgroundColor: isVideoMuted ? "rgba(255, 255, 255, 0.06)" : "rgba(99, 102, 241, 0.2)",
                  border: isVideoMuted ? "1px solid rgba(255, 255, 255, 0.12)" : "1px solid rgba(99, 102, 241, 0.4)",
                  color: isVideoMuted ? "#cbd5e1" : "#a5b4fc",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.15)")}
                onMouseOut={(e) => (e.currentTarget.style.backgroundColor = isVideoMuted ? "rgba(255, 255, 255, 0.06)" : "rgba(99, 102, 241, 0.2)")}
                aria-label={isVideoMuted ? "Unmute audio" : "Mute audio"}
              >
                {isVideoMuted ? (
                  <>
                    <VolumeX style={{ width: "12px", height: "12px" }} />
                    <span>Unmute</span>
                  </>
                ) : (
                  <>
                    <Volume2 style={{ width: "12px", height: "12px" }} />
                    <span>Sound On</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Video Player Display */}
          <div style={{ position: "relative", backgroundColor: "#060913", overflow: "hidden" }}>
            <video
              ref={videoRef}
              src="/promo.mp4"
              autoPlay
              muted
              loop
              playsInline
              preload="metadata"
              style={{
                width: "100%",
                height: "auto",
                maxHeight: "680px",
                display: "block",
                objectFit: "contain",
                margin: "0 auto",
                borderRadius: "0 0 18px 18px",
              }}
              onPlay={() => setIsVideoPlaying(true)}
              onPause={() => setIsVideoPlaying(false)}
            />
          </div>
        </div>
      </section>

      {/* 5. How It Works (3 Steps) */}
      <section id="how-it-works" style={{ padding: "5rem 1.5rem", maxWidth: "1240px", margin: "0 auto", borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
        <div style={{ textAlign: "center", marginBottom: "3.5rem" }}>
          <h2 style={{ fontSize: "clamp(2rem, 3.5vw, 2.5rem)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: "0.75rem" }}>
            How AnalyzaX Works in 3 Simple Steps
          </h2>
          <p style={{ fontSize: "1.0625rem", color: "#94a3b8" }}>From raw upload to executive presentation in under a minute.</p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "2rem",
          }}
        >
          <div style={{ textAlign: "center", padding: "1.5rem" }}>
            <div style={{ width: "52px", height: "52px", borderRadius: "50%", backgroundColor: "rgba(99, 102, 241, 0.15)", color: "#a5b4fc", border: "1px solid rgba(99, 102, 241, 0.3)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1.25rem", fontSize: "1.25rem", fontWeight: 700 }}>
              1
            </div>
            <h4 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "0.5rem" }}>Drop In Any Dataset</h4>
            <p style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.6 }}>
              Upload your CSV, Excel spreadsheet, or Parquet file. AnalyzaX automatically catalogs your data and verifies quality.
            </p>
          </div>

          <div style={{ textAlign: "center", padding: "1.5rem" }}>
            <div style={{ width: "52px", height: "52px", borderRadius: "50%", backgroundColor: "rgba(168, 85, 247, 0.15)", color: "#c084fc", border: "1px solid rgba(168, 85, 247, 0.3)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1.25rem", fontSize: "1.25rem", fontWeight: 700 }}>
              2
            </div>
            <h4 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "0.5rem" }}>Explore & Clean Automatically</h4>
            <p style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.6 }}>
              View distributions, resolve null values with 1-click recommendations, and build beautiful interactive visual dashboards.
            </p>
          </div>

          <div style={{ textAlign: "center", padding: "1.5rem" }}>
            <div style={{ width: "52px", height: "52px", borderRadius: "50%", backgroundColor: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.3)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1.25rem", fontSize: "1.25rem", fontWeight: 700 }}>
              3
            </div>
            <h4 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "0.5rem" }}>Predict & Share Outcomes</h4>
            <p style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.6 }}>
              Ask the AI Analyst for instant insights, forecast future performance with AutoML, and export boardroom reports.
            </p>
          </div>
        </div>
      </section>

      {/* 6. Call To Action Banner */}
      <section style={{ padding: "4rem 1.5rem 6rem", maxWidth: "1240px", margin: "0 auto" }}>
        <BorderGlow
          borderRadius={24}
          glowRadius={50}
          glowIntensity={1.2}
          edgeSensitivity={30}
          backgroundColor="rgba(15, 23, 42, 0.85)"
          colors={['#818cf8', '#c084fc', '#38bdf8']}
          animated
          style={{
            padding: "3.5rem 2rem",
            textAlign: "center",
            boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5)",
            position: "relative",
            overflow: "hidden",
            width: "100%",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "-50px",
              right: "-50px",
              width: "250px",
              height: "250px",
              borderRadius: "50%",
              backgroundColor: "rgba(99, 102, 241, 0.15)",
              filter: "blur(40px)",
              pointerEvents: "none",
            }}
          />

          <h2 style={{ fontSize: "clamp(2rem, 3.5vw, 2.75rem)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: "1rem" }}>
            Ready to Uncover What Your Data Is Really Telling You?
          </h2>
          <p style={{ fontSize: "1.125rem", color: "#cbd5e1", maxWidth: "620px", margin: "0 auto 2.25rem", lineHeight: 1.6 }}>
            Join analysts and teams using AnalyzaX to profile, clean, visualize, and forecast their data without complex coding.
          </p>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "1rem", flexWrap: "wrap" }}>
            <Link
              to="/register"
              style={{
                background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                color: "#ffffff",
                textDecoration: "none",
                fontSize: "1rem",
                fontWeight: 600,
                padding: "0.85rem 2rem",
                borderRadius: "10px",
                boxShadow: "0 10px 25px rgba(99, 102, 241, 0.5)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              Get Started for Free
              <ArrowRight style={{ width: "16px", height: "16px" }} />
            </Link>
            <Link
              to="/login"
              style={{
                backgroundColor: "rgba(15, 23, 42, 0.6)",
                color: "#cbd5e1",
                textDecoration: "none",
                fontSize: "1rem",
                fontWeight: 500,
                padding: "0.85rem 1.75rem",
                borderRadius: "10px",
                border: "1px solid rgba(255, 255, 255, 0.12)",
              }}
            >
              Sign In to Workspace
            </Link>
          </div>
        </BorderGlow>
      </section>

      {/* 7. Footer */}
      <footer style={{ borderTop: "1px solid rgba(255, 255, 255, 0.08)", padding: "3rem 1.5rem", backgroundColor: "rgba(11, 15, 25, 0.95)" }}>
        <div style={{ maxWidth: "1240px", margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <AnalyzaXLogo size={24} showText={true} />
            <span style={{ fontSize: "0.8125rem", color: "#64748b" }}>
              © {new Date().getFullYear()} AnalyzaX. All rights reserved.
            </span>
          </div>
          <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.8125rem", color: "#94a3b8" }}>
            <Link to="/login" style={{ color: "#94a3b8", textDecoration: "none" }}>Workspace Login</Link>
            <Link to="/register" style={{ color: "#94a3b8", textDecoration: "none" }}>Register</Link>
            <a href="#features" style={{ color: "#94a3b8", textDecoration: "none" }}>Features</a>
            <a href="#how-it-works" style={{ color: "#94a3b8", textDecoration: "none" }}>How It Works</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
