import Image from "next/image";

type Size = "sm" | "md" | "lg";

/** Heights are fixed per size; width follows the intrinsic aspect ratio. */
const MARK_H: Record<Size, number> = { sm: 24, md: 32, lg: 44 };
const FULL_H: Record<Size, number> = { sm: 44, md: 64, lg: 96 };

const MARK_RATIO = 480 / 260;
const FULL_RATIO = 720 / 552;

/**
 * `mark`  — the AIC symbol alone. The full lockup carries a wordmark and
 *           tagline that turn to mush below ~60px, so anything navbar-sized
 *           uses this.
 * `full`  — the complete lockup, for generous light surfaces (footer, about).
 *
 * Both assets are navy/green on transparency, so on the dark navbar the mark is
 * placed on a light plate rather than recoloured — inverting would break the
 * gradient and the dotted map.
 */
export default function Logo({
  size = "md",
  variant = "mark",
  plate = false,
}: {
  size?: Size;
  variant?: "mark" | "full";
  plate?: boolean;
}) {
  const isMark = variant === "mark";
  const h = isMark ? MARK_H[size] : FULL_H[size];
  const w = Math.round(h * (isMark ? MARK_RATIO : FULL_RATIO));

  const img = (
    <Image
      src={isMark ? "/aic-mark.png" : "/aic-logo.png"}
      alt="African Intelligence Cloud"
      width={w}
      height={h}
      priority
      className="h-full w-auto object-contain"
    />
  );

  if (plate) {
    return (
      <span
        className="inline-flex items-center rounded-xl bg-white px-2.5 py-1.5 shadow-sm"
        style={{ height: h + 12 }}
      >
        <span className="block" style={{ height: h }}>
          {img}
        </span>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center" style={{ height: h }}>
      {img}
    </span>
  );
}
