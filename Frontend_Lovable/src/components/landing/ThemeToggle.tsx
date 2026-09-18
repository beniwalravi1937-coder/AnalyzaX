import React, { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

interface ThemeToggleProps {
  className?: string;
  style?: React.CSSProperties;
}

export function ThemeToggle({ className = "", style = {} }: ThemeToggleProps) {
  const { theme, toggleTheme, isDark } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Until mounted, render a placeholder of the exact same 38px dimensions to prevent hydration mismatch/layout shifts
  if (!mounted) {
    return (
      <div
        style={{
          width: "38px",
          height: "38px",
          borderRadius: "10px",
          border: "1px solid transparent",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          visibility: "hidden",
          ...style,
        }}
        aria-hidden="true"
        className={className}
      />
    );
  }

  const nextModeText = isDark ? "light" : "dark";
  const ariaLabel = `Switch to ${nextModeText} mode`;

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={ariaLabel}
      title={ariaLabel}
      className={`theme-toggle-btn ${className}`}
      style={{
        width: "38px",
        height: "38px",
        borderRadius: "10px",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.1))",
        backgroundColor: "transparent",
        color: "var(--text-secondary, #94a3b8)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        position: "relative",
        overflow: "hidden",
        padding: 0,
        outline: "none",
        transition: "background-color 200ms ease, border-color 200ms ease, color 200ms ease, transform 150ms ease",
        ...style,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--bg-elevated, rgba(255, 255, 255, 0.07))";
        e.currentTarget.style.borderColor = "var(--border-default, rgba(255, 255, 255, 0.2))";
        e.currentTarget.style.color = "var(--text-primary, #ffffff)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "transparent";
        e.currentTarget.style.borderColor = "var(--border-subtle, rgba(255, 255, 255, 0.1))";
        e.currentTarget.style.color = "var(--text-secondary, #94a3b8)";
      }}
      onFocus={(e) => {
        e.currentTarget.style.boxShadow = "0 0 0 2px var(--accent, #6366f1)";
      }}
      onBlur={(e) => {
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <span
        style={{
          position: "relative",
          width: "18px",
          height: "18px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Sun Icon (displayed in Dark mode to indicate switching to Light) */}
        <Sun
          style={{
            position: "absolute",
            width: "18px",
            height: "18px",
            color: "var(--warning, #fbbf24)",
            transform: isDark ? "rotate(0deg) scale(1)" : "rotate(90deg) scale(0)",
            opacity: isDark ? 1 : 0,
            transition: "transform 220ms cubic-bezier(0.4, 0, 0.2, 1), opacity 220ms ease",
            pointerEvents: "none",
          }}
          aria-hidden="true"
        />

        {/* Moon Icon (displayed in Light mode to indicate switching to Dark) */}
        <Moon
          style={{
            position: "absolute",
            width: "18px",
            height: "18px",
            color: "var(--accent, #4f46e5)",
            transform: !isDark ? "rotate(0deg) scale(1)" : "rotate(-90deg) scale(0)",
            opacity: !isDark ? 1 : 0,
            transition: "transform 220ms cubic-bezier(0.4, 0, 0.2, 1), opacity 220ms ease",
            pointerEvents: "none",
          }}
          aria-hidden="true"
        />
      </span>
    </button>
  );
}
