"use server";

import { revalidatePath } from "next/cache";
import { postFeedback, postRun, type RunRequest } from "@/lib/api";
import type { Override, RunResponse } from "@/lib/types";

/**
 * Run the pipeline. After persistence, invalidate the home page so the
 * new run appears in the "Recent runs" panel without a hard reload.
 */
export async function runPipelineAction(input: RunRequest): Promise<RunResponse> {
  const response = await postRun(input);
  revalidatePath("/");
  revalidatePath("/runs");
  return response;
}

/**
 * Capture an operator routing override. Triggers revalidation of the
 * single-run page so the override surfaces immediately.
 */
export async function recordOverrideAction(
  leadResultId: string,
  correctedOwner: string,
  reason?: string,
): Promise<Override> {
  const result = await postFeedback(leadResultId, {
    corrected_owner: correctedOwner,
    operator_id: "ui",
    reason: reason ?? "submitted via operator console",
  });
  revalidatePath("/");
  revalidatePath("/runs/[id]", "page");
  return result;
}
