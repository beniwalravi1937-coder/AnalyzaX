"""
AnalyzaX — Phase 24: SSRF (Server-Side Request Forgery) Guard.
Validates outbound URLs, resolving DNS hostnames and enforcing that outbound network requests
cannot reach localhost, link-local, cloud metadata services (e.g. 169.254.169.254), or private RFC 1918 subnets.
"""

import ipaddress
import socket
from typing import List, Optional, Set, Tuple
from urllib.parse import urlparse

# Explicit disallowed IP networks
BLOCKED_NETWORKS = [
    # IPv4 Loopback & Private
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Cloud metadata & Link-local
    ipaddress.ip_network("169.254.0.0/16"),
    # Broadcast & Multicast
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6 Loopback & Private / Link-local
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::/128"),
]

ALLOWED_SCHEMES = {"http", "https"}


class SSRFGuard:
    """Validates destination URLs and hostnames against SSRF risks."""

    @classmethod
    def is_ip_blocked(cls, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Evaluates whether an IP address is private, loopback, link-local, or reserved."""
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return True

        for net in BLOCKED_NETWORKS:
            if ip in net:
                return True
        return False

    @classmethod
    def resolve_and_validate_host(cls, hostname: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Resolves DNS records for hostname and ensures NO resolved IP is in a blocked network.
        Defends against DNS rebinding and internal subnet pivoting.
        Returns: (is_safe: bool, error_message: Optional[str], resolved_ips: List[str])
        """
        if not hostname:
            return False, "Hostname cannot be empty", []

        clean_host = hostname.strip().lower().strip("[]")

        # First check if hostname is directly an IP literal
        try:
            ip = ipaddress.ip_address(clean_host)
            if cls.is_ip_blocked(ip):
                return False, f"Direct access to private or restricted IP '{clean_host}' is prohibited", [str(ip)]
            return True, None, [str(ip)]
        except ValueError:
            # Not an IP literal, proceed to DNS resolution
            pass

        # Check explicit localhost patterns
        if clean_host in ("localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"):
            return False, "Access to localhost is prohibited", []

        try:
            addr_info = socket.getaddrinfo(clean_host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
            resolved_ips: List[str] = []

            for family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                resolved_ips.append(ip_str)
                try:
                    ip = ipaddress.ip_address(ip_str)
                    if cls.is_ip_blocked(ip):
                        return (
                            False,
                            f"SSRF violation: Host '{clean_host}' resolves to restricted IP '{ip_str}'",
                            resolved_ips,
                        )
                except ValueError:
                    return False, f"Invalid resolved IP format: '{ip_str}'", resolved_ips

            if not resolved_ips:
                return False, f"Unable to resolve hostname '{clean_host}'", []

            return True, None, resolved_ips

        except socket.gaierror as e:
            return False, f"DNS resolution failed for '{clean_host}': {e}", []
        except Exception as e:
            return False, f"DNS check error for '{clean_host}': {e}", []

    @classmethod
    def check_url(
        cls,
        url: str,
        allowed_schemes: Optional[Set[str]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive URL security check.
        Enforces scheme whitelist, prevents credentials in URLs, and validates DNS resolution.
        Returns (is_safe, error_message).
        """
        if not url or not url.strip():
            return False, "URL cannot be empty"

        schemes = allowed_schemes or ALLOWED_SCHEMES
        try:
            parsed = urlparse(url.strip())
        except Exception as e:
            return False, f"Malformed URL: {e}"

        if not parsed.scheme or parsed.scheme.lower() not in schemes:
            return False, f"Scheme '{parsed.scheme}' is not allowed. Allowed: {sorted(list(schemes))}"

        if not parsed.hostname:
            return False, "URL must include a valid hostname"

        # Disallow credentials in URL (e.g. http://user:pass@host)
        if parsed.username or parsed.password:
            return False, "URLs containing embedded userinfo credentials are not permitted"

        # Validate hostname & resolved IPs
        is_safe, err, _ = cls.resolve_and_validate_host(parsed.hostname)
        if not is_safe:
            return False, err

        return True, None

    @classmethod
    def validate_url(
        cls,
        url: str,
        allowed_schemes: Optional[Set[str]] = None,
    ) -> str:
        """
        Validates URL and raises ValueError if the URL violates SSRF or security boundaries.
        Returns the clean validated URL if safe.
        """
        is_safe, err = cls.check_url(url, allowed_schemes)
        if not is_safe:
            raise ValueError(err or "SSRF violation: target destination is restricted")
        return url.strip()

    @classmethod
    def is_safe_url(cls, url: str) -> bool:
        """Convenience method returning True if URL is safe, False otherwise."""
        is_safe, _ = cls.check_url(url)
        return is_safe


ssrf_guard = SSRFGuard()
