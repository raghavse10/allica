"""Deterministic first-touch copy; default path and LLM fallback."""

from __future__ import annotations

from ..sectors import DEFAULT_SECTOR_PROP, SECTOR_PROPS
from .context import EmailContext


def _history_clause(ctx: EmailContext) -> str:
    if ctx.incorporated_on:
        return (
            f"With {ctx.company_name} trading since {ctx.incorporated_on[:4]}, "
            "we can usually move from an initial chat to a shortlist of options "
            "without a drawn-out underwriting process."
        )
    return (
        f"For an established business like {ctx.company_name}, we can "
        "usually move from an initial chat to a shortlist of options "
        "without a drawn-out underwriting process."
    )


def render_template(ctx: EmailContext) -> tuple[str, str]:
    sector_prop, _product = SECTOR_PROPS.get(ctx.sector or "", DEFAULT_SECTOR_PROP)

    subject = f"{ctx.company_name}: a quick note on {ctx.inferred_need}"
    body = (
        f"Hi {ctx.contact_first_name},\n\n"
        f"Thanks for getting in touch. I picked up your enquiry about "
        f"{ctx.inferred_need} for {ctx.company_name} and wanted to introduce "
        f"myself before suggesting a next step.\n\n"
        f"{sector_prop} so the conversation tends to move faster than with a "
        f"general lender. {_history_clause(ctx)}\n\n"
        f"If it would help, I can share a couple of structures that suit a "
        f"business of your size and walk through the information we would "
        f"typically need to see. Would a short 20-minute call next week work "
        f"for you?\n\n"
        f"Best regards,\nThe Allica Team"
    )
    return subject, body
