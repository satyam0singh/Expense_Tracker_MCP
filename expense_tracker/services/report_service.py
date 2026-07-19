"""Report Service.

Handles generating data exports (CSV, Excel) for expenses.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.logging import get_logger
from expense_tracker.repositories.expense_repository import ExpenseRepository
from expense_tracker.services.base import BaseService

logger = get_logger(__name__)


class ReportService(BaseService):
    """Service for generating expense reports and data exports."""

    def __init__(self, expense_repo: ExpenseRepository | None = None) -> None:
        """Initialize the report service.

        Args:
            expense_repo: Optional ExpenseRepository.
        """
        super().__init__()
        self.expense_repo = expense_repo or ExpenseRepository()

    async def generate_csv_report(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        user_id: uuid.UUID,
    ) -> str:
        """Generate a CSV report of expenses for a date range.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: The UUID of the user.

        Returns:
            CSV file content as a string.
        """
        # We need all records, so limit=10000 (practical limit for CSV export via MCP)
        # For a truly massive export, this would be paginated and written to a file.
        expenses, _ = await self.expense_repo.find_by_date_range(
            session=session,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            limit=10000, 
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Date",
            "Category",
            "Subcategory",
            "Title",
            "Amount",
            "Currency",
            "Payment Method",
            "Notes"
        ])

        # Rows
        for expense in expenses:
            category_name = expense.category.display_name if expense.category else ""
            subcategory_name = expense.subcategory.display_name if expense.subcategory else ""
            
            writer.writerow([
                expense.expense_date.isoformat(),
                category_name,
                subcategory_name,
                expense.title,
                f"{expense.amount:.2f}",
                expense.currency,
                expense.payment_method,
                expense.notes or ""
            ])

        return output.getvalue()

    async def generate_excel_report(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        user_id: uuid.UUID,
    ) -> bytes:
        """Generate an Excel report of expenses for a date range.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: The UUID of the user.

        Returns:
            Excel file content as bytes.
        """
        import openpyxl
        from openpyxl.styles import Font, Alignment

        expenses, _ = await self.expense_repo.find_by_date_range(
            session=session,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            limit=10000, 
        )

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Expenses"

        # Headers
        headers = ["Date", "Category", "Subcategory", "Title", "Amount", "Currency", "Payment Method", "Notes"]
        ws.append(headers)
        
        # Style headers
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Data
        for expense in expenses:
            ws.append([
                expense.expense_date.isoformat(),
                expense.category.display_name if expense.category else "",
                expense.subcategory.display_name if expense.subcategory else "",
                expense.title,
                float(expense.amount),
                expense.currency,
                expense.payment_method,
                expense.notes or ""
            ])

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    async def generate_pdf_report(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        user_id: uuid.UUID,
    ) -> bytes:
        """Generate a PDF report of expenses for a date range.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: The UUID of the user.

        Returns:
            PDF file content as bytes.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        expenses, _ = await self.expense_repo.find_by_date_range(
            session=session,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            limit=10000, 
        )

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_text = f"Expense Report ({start_date.isoformat()} to {end_date.isoformat()})"
        elements.append(Paragraph(title_text, styles['Title']))
        elements.append(Spacer(1, 12))

        # Data for Table
        data = [["Date", "Category", "Title", "Amount", "Method"]]
        total_amount = 0.0

        for expense in expenses:
            data.append([
                expense.expense_date.isoformat(),
                expense.category.display_name if expense.category else "",
                expense.title,
                f"{expense.currency} {float(expense.amount):.2f}",
                expense.payment_method
            ])
            total_amount += float(expense.amount)

        # Append Total Row
        data.append(["", "", "Total:", f"{total_amount:.2f}", ""])

        # Create Table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (2, -1), (2, -1), 'Helvetica-Bold'), # Total label
            ('FONTNAME', (3, -1), (3, -1), 'Helvetica-Bold'), # Total amount
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return output.getvalue()
