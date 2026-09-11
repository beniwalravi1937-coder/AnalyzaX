"""
Invoice & Payment History Service for Phase 21: Billing.
Provides authorized, paginated invoice and transaction history.
"""

from typing import List, Optional

from backend.app.engines.billing.models import (
    Invoice,
    InvoiceListResponse,
    Payment,
)
from backend.app.engines.billing.repository import BillingRepository, billing_repository


class BillingInvoiceService:
    """Manages workspace invoices and payment history."""

    def __init__(self, repo: Optional[BillingRepository] = None):
        self._repo = repo or billing_repository

    def list_invoices(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> InvoiceListResponse:
        """Retrieves paginated invoices for a workspace."""
        invoices, total = self._repo.list_invoices_by_workspace(workspace_id, limit=limit, offset=offset)
        return InvoiceListResponse(
            invoices=invoices,
            total=total,
            has_more=(offset + len(invoices)) < total,
        )

    def get_invoice(self, workspace_id: str, external_invoice_id: str) -> Optional[Invoice]:
        """Retrieves an invoice guaranteeing workspace ownership (preventing IDOR)."""
        inv = self._repo.get_invoice_by_external_id("sandbox", external_invoice_id)
        if not inv:
            inv = self._repo.get_invoice_by_external_id("stripe", external_invoice_id)

        if inv and inv.workspace_id == workspace_id:
            return inv
        return None

    def list_payments(self, workspace_id: str) -> List[Payment]:
        """Lists discrete payments for a workspace."""
        return self._repo.list_payments_by_workspace(workspace_id)


# Global invoice service instance
invoice_service = BillingInvoiceService()
