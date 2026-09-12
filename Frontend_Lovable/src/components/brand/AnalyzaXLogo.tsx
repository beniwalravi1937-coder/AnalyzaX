import React from "react";
import logoImg from "../../assets/logo.png";

interface AnalyzaXLogoProps {
  size?: number;
  showText?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function AnalyzaXLogo({
  size = 28,
  showText = false,
  className = "",
  style = {},
}: AnalyzaXLogoProps) {
  return (
    <span
      className={`brand-logo-container ${className}`}
      style={{ display: "inline-flex", alignItems: "center", gap: "0.55rem", ...style }}
    >
      <img
        src={logoImg}
        alt="AnalyzaX Logo"
        width={size}
        height={size}
        style={{
          width: `${size}px`,
          height: `${size}px`,
          objectFit: "contain",
          filter: "drop-shadow(0 2px 10px rgba(59, 130, 246, 0.45))",
          flexShrink: 0,
        }}
      />
      {showText && (
        <span
          style={{
            fontWeight: 800,
            letterSpacing: "-0.02em",
            color: "#ffffff",
            fontSize: "1.15rem",
            lineHeight: 1,
            fontFamily: '"Space Grotesk", sans-serif',
          }}
        >
          Analyza
          <span
            style={{
              background: "linear-gradient(135deg, #60a5fa 0%, #a855f7 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            X
          </span>
        </span>
      )}
    </span>
  );
}

export default AnalyzaXLogo;
