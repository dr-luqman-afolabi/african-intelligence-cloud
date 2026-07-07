export default function Spinner({ size = 8 }: { size?: number }) {
  return (
    <div
      className="animate-spin rounded-full border-aic-green border-t-transparent"
      style={{ width: size * 4, height: size * 4, borderWidth: Math.max(2, size / 3) }}
    />
  );
}
