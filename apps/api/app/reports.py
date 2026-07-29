from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from .analytics import (
    attribution_analytics,
    exposure_analytics,
    holdings_snapshot,
    performance_analytics,
)


def report_payload(
    db: Session, portfolio_id: str, owner_id: str
) -> dict[str, Any]:
    return {
        "holdings": holdings_snapshot(db, portfolio_id, owner_id),
        "performance": performance_analytics(db, portfolio_id, owner_id),
        "exposure": exposure_analytics(db, portfolio_id, owner_id),
        "attribution": attribution_analytics(db, portfolio_id, owner_id),
    }


def build_pdf(payload: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="AssetLens Portfolio Research Report",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Metric",
            parent=styles["BodyText"],
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#102a43"),
        )
    )
    story = [
        Paragraph("AssetLens", styles["Title"]),
        Paragraph("Portfolio Research Report", styles["Heading2"]),
    ]
    snapshot = payload["holdings"]
    performance = payload["performance"]
    exposure = payload["exposure"]
    portfolio = snapshot["portfolio"]
    story.extend(
        [
            Paragraph(f"<b>{portfolio['name']}</b>", styles["Heading3"]),
            Paragraph(
                f"Benchmark: {portfolio['benchmark_name']} &nbsp;&nbsp; Data through: {snapshot['as_of']}",
                styles["BodyText"],
            ),
            Spacer(1, 12),
        ]
    )
    summary = snapshot["summary"]
    metrics = performance["metrics"]
    summary_data = [
        [
            "Market value",
            f"${summary['market_value']:,.2f}",
            "Period return",
            f"{metrics['time_weighted_return']:.2%}",
        ],
        [
            "Cost basis",
            f"${summary['cost_basis']:,.2f}",
            "Benchmark return",
            f"{metrics['benchmark_return']:.2%}",
        ],
        [
            "Unrealized gain",
            f"${summary['unrealized_gain']:,.2f}",
            "Maximum drawdown",
            f"{metrics['maximum_drawdown']:.2%}",
        ],
        [
            "Volatility",
            f"{metrics['annualized_volatility']:.2%}",
            "Sharpe ratio",
            f"{metrics['sharpe_ratio']:.2f}",
        ],
    ]
    summary_table = Table(summary_data, colWidths=[1.25 * inch, 1.25 * inch] * 2)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f6f8")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5df")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 16), Paragraph("Holdings", styles["Heading2"])])
    holdings_data = [["Symbol", "Name", "Sector", "Weight", "Value", "Return"]]
    for item in snapshot["holdings"]:
        holdings_data.append(
            [
                item["symbol"],
                item["name"][:30],
                item["sector"],
                f"{item['weight']:.1%}",
                f"${item['market_value']:,.0f}",
                f"{item['unrealized_return']:.1%}",
            ]
        )
    holdings_table = Table(
        holdings_data,
        repeatRows=1,
        colWidths=[0.55 * inch, 1.75 * inch, 1.05 * inch, 0.65 * inch, 0.9 * inch, 0.65 * inch],
    )
    holdings_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123c3a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fa")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8e0e5")),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([holdings_table, Spacer(1, 16), Paragraph("Sector allocation", styles["Heading2"])])
    sector_data = [["Sector", "Weight", "Market value"]]
    for item in exposure["allocation"]["sector"]:
        sector_data.append([item["name"], f"{item['weight']:.1%}", f"${item['value']:,.0f}"])
    sector_table = Table(sector_data, colWidths=[2.4 * inch, 1.1 * inch, 1.3 * inch])
    sector_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d8a84e")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8e0e5")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend(
        [
            sector_table,
            Spacer(1, 16),
            Paragraph("Methodology and limitations", styles["Heading2"]),
            Paragraph(
                "Returns use seeded daily closing prices and static quantities. Volatility is annualized "
                "from daily observations using 252 trading days. Scenario results are simplified "
                "instantaneous shocks, not forecasts. This report is for software demonstration and "
                "educational research only and is not investment advice.",
                styles["BodyText"],
            ),
            Spacer(1, 8),
            Paragraph(
                f"Calculated at {performance['calculated_at']}. Report inputs are reproducible from the "
                "authenticated AssetLens analytics endpoints.",
                styles["BodyText"],
            ),
        ]
    )
    doc.build(story)
    return buffer.getvalue()
