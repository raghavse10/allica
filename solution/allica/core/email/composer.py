"""Pick template vs LLM, run safety, enforce single-CTA policy for LLM path."""

from __future__ import annotations

from ..safety import count_ctas, sanitise_email
from ..schemas import EmailDraft, Enrichment, InboundLead, SafetyFlag
from ..text_utils import count_words
from .context import EmailContext, build_context
from .llm import generate_email_via_llm
from .template import render_template


def _make_draft(
    subject: str,
    body: str,
    flags: list[SafetyFlag],
    used_disclaimer: bool,
    generator: str,
) -> EmailDraft:
    return EmailDraft(
        subject=subject,
        body=body,
        word_count=count_words(body),
        cta_count=count_ctas(body),
        used_disclaimer=used_disclaimer,
        generator=generator,  # type: ignore[arg-type]
    )


def _generate_template(
    ctx: EmailContext,
) -> tuple[str, str, list[SafetyFlag], bool]:
    subject, body = render_template(ctx)
    return sanitise_email(subject, body)


def compose_email(
    lead: InboundLead, enrichment: Enrichment, *, prefer_llm: bool = False
) -> tuple[EmailDraft, list[SafetyFlag]]:
    ctx = build_context(lead, enrichment)

    if not prefer_llm:
        subject, body, flags, disc = _generate_template(ctx)
        return _make_draft(subject, body, flags, disc, "template"), flags

    llm_outcome = generate_email_via_llm(ctx, lead)
    if llm_outcome is None:
        subject, body, flags, disc = _generate_template(ctx)
        return _make_draft(subject, body, flags, disc, "template"), flags

    (subject, body), provider_name = llm_outcome
    subject, body, flags, disc = sanitise_email(subject, body)

    # If sanitisation hit a hard block, the LLM produced something we are
    # *not* willing to ship even after rewriting. Fall back to the template
    # entirely so we never send a half-rewritten model output.
    if any(f.severity == "block" for f in flags):
        t_subject, t_body, t_flags, t_disc = _generate_template(ctx)
        flags = flags + [
            SafetyFlag(
                code="llm_fallback",
                severity="warning",
                message=f"{provider_name} output contained banned phrases; reverted to template.",
            )
        ] + t_flags
        return _make_draft(t_subject, t_body, flags, t_disc, "template"), flags

    # Playbook: exactly one clear CTA. The template path guarantees this;
    # LLM output can stack multiple asks — same policy as hard blocks: ship
    # the deterministic draft instead of a confusing multi-ask model email.
    if count_ctas(body) != 1:
        t_subject, t_body, t_flags, t_disc = _generate_template(ctx)
        n = count_ctas(body)
        flags = flags + [
            SafetyFlag(
                code="llm_cta_count",
                severity="warning",
                message=(
                    f"{provider_name} draft had {n} call-to-action cue(s) after "
                    "sanitisation (expected 1); reverted to template."
                ),
            )
        ] + t_flags
        return _make_draft(t_subject, t_body, flags, t_disc, "template"), flags

    generator = "llm+sanitised" if flags else "llm"
    return _make_draft(subject, body, flags, disc, generator), flags
