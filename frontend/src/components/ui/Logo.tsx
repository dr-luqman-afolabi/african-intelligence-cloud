export default function Logo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const bar = size === "lg" ? "w-2 h-9" : size === "sm" ? "w-1 h-4" : "w-1.5 h-6";
  const text = size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg";
  return (
    <span className="flex items-center gap-2.5 font-bold tracking-tight">
      <span className="flex gap-0.5">
        <span className={`${bar} rounded-full bg-aic-green`} />
        <span className={`${bar} rounded-full bg-aic-gold`} />
        <span className={`${bar} rounded-full bg-aic-red`} />
      </span>
      <span className={text}>AIC</span>
    </span>
  );
}
