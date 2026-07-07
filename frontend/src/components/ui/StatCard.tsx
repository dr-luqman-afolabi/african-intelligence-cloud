interface Props {
  label: string;
  value: string;
  hint?: string;
  icon?: React.ReactNode;
  accent?: "green" | "gold" | "red" | "slate";
}

const ACCENTS: Record<string, string> = {
  green: "bg-aic-green/10 text-aic-green",
  gold: "bg-aic-gold/15 text-amber-700",
  red: "bg-aic-red/10 text-aic-red",
  slate: "bg-slate-100 text-slate-600",
};

export default function StatCard({ label, value, hint, icon, accent = "green" }: Props) {
  return (
    <div className="card card-hover p-5 animate-fade-in-up">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-1.5 text-2xl font-bold text-aic-dark tabular-nums">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        {icon && (
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${ACCENTS[accent]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
