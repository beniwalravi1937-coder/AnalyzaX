import React from "react";
import { Link as TanstackLink, useNavigate, useRouterState } from "@tanstack/react-router";

export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href?: string;
  to?: string;
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const Link = React.forwardRef<HTMLAnchorElement, LinkProps>(
  ({ href, to, children, className, style, onClick, ...rest }, ref) => {
    const target = to || href || "/";
    return (
      <TanstackLink
        ref={ref}
        to={target as any}
        className={className}
        style={style}
        onClick={onClick}
        {...(rest as any)}
      >
        {children}
      </TanstackLink>
    );
  }
);
Link.displayName = "NextCompatLink";

export default Link;

export function useRouter() {
  const navigate = useNavigate();
  return {
    push: (url: string) => {
      navigate({ to: url as any });
    },
    replace: (url: string) => {
      navigate({ to: url as any, replace: true });
    },
    back: () => {
      if (typeof window !== "undefined") window.history.back();
    },
    forward: () => {
      if (typeof window !== "undefined") window.history.forward();
    },
    refresh: () => {
      if (typeof window !== "undefined") window.location.reload();
    },
    prefetch: () => {},
  };
}

export function usePathname(): string {
  try {
    return useRouterState({ select: (s) => s.location.pathname });
  } catch {
    return typeof window !== "undefined" ? window.location.pathname : "/";
  }
}

export function useSearchParams(): URLSearchParams {
  if (typeof window !== "undefined") {
    return new URLSearchParams(window.location.search);
  }
  return new URLSearchParams();
}

export function Image({
  src,
  alt = "",
  width,
  height,
  className,
  style,
  ...rest
}: React.ImgHTMLAttributes<HTMLImageElement> & { width?: number | string; height?: number | string }) {
  return (
    <img
      src={src}
      alt={alt}
      width={width}
      height={height}
      className={className}
      style={style}
      {...rest}
    />
  );
}
