"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState, useTransition } from "react";
import { runPipelineAction } from "@/app/actions";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import type { RunResponse } from "@/lib/types";

interface RunControlsProps {
  onResult: (response: RunResponse) => void;
}

/**
 * Client island that drives the pipeline. Owns three pieces of UI state:
 *  - draft_email / prefer_llm flags
 *  - the optional "custom JSON" textarea (collapsed by default)
 *  - the in-flight + error states for the run
 */
export function RunControls({ onResult }: RunControlsProps) {
  const [draftEmail, setDraftEmail] = useState(true);
  const [preferLlm, setPreferLlm] = useState(false);
  const [customOpen, setCustomOpen] = useState(false);
  const [customJson, setCustomJson] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function trigger(leads?: unknown[]) {
    setError(null);
    startTransition(async () => {
      try {
        const response = await runPipelineAction({
          leads,
          draft_email: draftEmail,
          prefer_llm: preferLlm,
        });
        onResult(response);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    });
  }

  function runCustom() {
    let leads: unknown[];
    try {
      leads = JSON.parse(customJson);
    } catch (e) {
      setError(`Invalid JSON: ${e instanceof Error ? e.message : String(e)}`);
      return;
    }
    if (!Array.isArray(leads)) {
      setError("Custom payload must be a JSON array of leads.");
      return;
    }
    trigger(leads);
  }

  return (
    <Card>
      <CardTitle>Run pipeline</CardTitle>
      <p className="text-xs text-ink-muted ">
        Submit leads to the assistant and inspect the output.
      </p>

      <div className="mt-4 space-y-2">
        <label className="flex cursor-pointer items-center gap-2.5 text-[13px] text-ink">
          <input
            type="checkbox"
            checked={draftEmail}
            onChange={(e) => setDraftEmail(e.target.checked)}
            className="h-4 w-4 cursor-pointer accent-brand-orange"
          />
          <span>Draft first-touch emails</span>
        </label>
        <label className="flex cursor-pointer items-center gap-2.5 text-[13px] text-ink">
          <input
            type="checkbox"
            checked={preferLlm}
            onChange={(e) => setPreferLlm(e.target.checked)}
            className="h-4 w-4 cursor-pointer accent-brand-orange"
          />
          <span>Prefer LLM</span>
        </label>
      </div>

      <div className="mt-4 flex flex-col gap-2">
        <Button onClick={() => trigger()} disabled={pending} block>
          {pending ? "Running…" : "Run on sample data"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCustomOpen((v) => !v)}
          disabled={pending}
          className="gap-1.5"
        >
          {customOpen ? (
            <>
              Hide custom JSON
              <ChevronUp className="h-5 w-5 shrink-0" strokeWidth={1} aria-hidden />
            </>
          ) : (
            <>
              Run custom JSON
              <ChevronDown className="h-5 w-5 shrink-0" strokeWidth={1} aria-hidden />
            </>
          )}
        </Button>
      </div>

      {customOpen && (
        <div className="mt-3">
          <textarea
            value={customJson}
            onChange={(e) => setCustomJson(e.target.value)}
            spellCheck={false}
            placeholder='[{"id": "L-1", "company_name": "Acme Ltd", ...}]'
            className="h-44 w-full resize-y rounded-lg border border-line bg-brand-cream-100 p-3 font-mono text-xs text-brand-navy placeholder:text-ink-subtle focus:border-brand-orange focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          />
          <Button
            onClick={runCustom}
            disabled={pending || !customJson.trim()}
            size="sm"
            className="mt-2"
          >
            Run
          </Button>
        </div>
      )}

      {error && (
        <div className="mt-3 rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          {error}
        </div>
      )}
    </Card>
  );
}
