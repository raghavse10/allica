import { Card, CardTitle } from "@/components/ui/Card";
import { RunsTable } from "@/components/RunsTable";

export default function RunsPage() {
  return (
    <Card>
      <CardTitle>All runs</CardTitle>
      <p className="text-xs text-ink-muted">
        Every persisted pipeline execution. Click a row for full detail.
      </p>

      <RunsTable />
    </Card>
  );
}
