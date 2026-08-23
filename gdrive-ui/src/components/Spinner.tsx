interface SpinnerProps {
  size?: number
  color?: string
}

export function Spinner({ size = 18, color = "var(--color-accent)" }: SpinnerProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ animation: "spinner-rotate 0.7s linear infinite" }}
    >
      <circle cx="12" cy="12" r="9" stroke={color} strokeOpacity="0.18" strokeWidth="3" />
      <path
        d="M21 12a9 9 0 0 0-9-9"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  )
}
