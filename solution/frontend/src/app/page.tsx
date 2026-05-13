import { HomeShell } from "@/components/HomeShell";
import { Legend } from "@/components/Legend";
import { RecentRuns } from "@/components/RecentRuns";

// Always render fresh — operator workflows depend on seeing the latest data.
export const dynamic = "force-dynamic";

export default function HomePage() {
  // Server components passed as props to a client component: Next 15's RSC
  // composition pattern. The client island never re-renders these.
  return <HomeShell recentRuns={<RecentRuns />} legend={<Legend />} />;
}
