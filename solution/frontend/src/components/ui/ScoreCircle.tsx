import { CSSProperties } from "react";

interface ScoreCircleProps {
  value: number;
}

export function ScoreCircle({ value }: ScoreCircleProps) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="score-circle" style={{ "--p": pct } as CSSProperties}>
      <span>{value.toFixed(2)}</span>
    </div>
  );
}
