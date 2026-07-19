"""Credit Card MCP Tools.

Registers endpoints for managing credit cards and tracking usage.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastmcp import FastMCP

from expense_tracker.core.exceptions import AppException
from expense_tracker.database.session import get_session
from expense_tracker.schemas.credit_card import (
    CreditCardCreate,
    CreditCardUpdate,
    CreditCardUsageUpdate,
)
from expense_tracker.services.credit_card_service import CreditCardService
from expense_tracker.core.constants import get_system_user_id
from expense_tracker.utils.response import error_response, success_response

SYSTEM_USER_ID = get_system_user_id()


def register_credit_card_tools(mcp: FastMCP) -> None:
    """Register credit card tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    card_service = CreditCardService()

    @mcp.tool()
    async def add_credit_card(
        card_name: str,
        last_four: str,
        limit: float,
        network: str = "other",
        billing_day: int = 1,
    ) -> dict[str, Any]:
        """Add a new credit card to track usage and limits.
        
        Args:
            card_name: Name of the card (e.g., 'HDFC Regalia').
            last_four: Last 4 digits of the card.
            limit: Total credit limit.
            network: Card network (e.g., 'visa', 'mastercard', 'amex').
            billing_day: Day of month the billing cycle starts (1-31).
        """
        try:
            async with get_session() as session:
                data = CreditCardCreate(
                    card_name=card_name,
                    last_four_digits=last_four,
                    credit_limit=limit,  # type: ignore[arg-type]
                    card_network=network,  # type: ignore[arg-type]
                    billing_cycle_day=billing_day,
                )
                
                card = await card_service.create_card(
                    session, user_id=SYSTEM_USER_ID, data=data
                )
                
                return success_response(
                    data={"card_id": str(card.id)},
                    message=f"Added credit card '{card.card_name}'."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def record_card_payment(
        card_id: str,
        amount: float,
    ) -> dict[str, Any]:
        """Record a payment made to a credit card to free up limit.
        
        Args:
            card_id: The UUID of the credit card.
            amount: The payment amount.
        """
        try:
            async with get_session() as session:
                data = CreditCardUsageUpdate(
                    amount=amount,  # type: ignore[arg-type]
                    is_payment=True,
                )
                
                card = await card_service.update_usage(
                    session,
                    card_id=uuid.UUID(card_id),
                    user_id=SYSTEM_USER_ID,
                    data=data,
                )
                
                return success_response(
                    message=f"Payment recorded. Available limit is now {card.available_limit}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def get_active_cards() -> dict[str, Any]:
        """List all active credit cards with their current usage and limits."""
        try:
            async with get_session() as session:
                cards = await card_service.get_active_cards(
                    session, user_id=SYSTEM_USER_ID
                )
                
                return success_response(
                    data=[
                        {
                            "id": str(c.id),
                            "name": c.card_name,
                            "limit": float(c.credit_limit),
                            "used": float(c.used_amount),
                            "available": float(c.available_limit),
                            "utilization": round(c.utilization_pct, 2),
                        }
                        for c in cards
                    ],
                    message=f"Found {len(cards)} active cards."
                )
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")
