import type { ReactNode } from "react"
import { CloseIcon } from "./icons"

interface DetailsPanelProps {
  title: string
  typeBadge?: ReactNode
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
}

export function DetailsPanel({ title, typeBadge, onClose, children, footer }: DetailsPanelProps) {
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        bottom: 0,
        width: 380,
        maxWidth: "92vw",
        background: "var(--color-surface)",
        borderLeft: "1px solid var(--color-border)",
        boxShadow: "var(--shadow-lg)",
        zIndex: 40,
        display: "flex",
        flexDirection: "column",
        animation: "modal-pop-in 0.16s var(--ease)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 12,
          padding: "20px 20px 16px",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        <div style={{ minWidth: 0 }}>
          {typeBadge}
          <div
            style={{
              fontSize: 15.5,
              fontWeight: 650,
              marginTop: 8,
              wordBreak: "break-word",
              lineHeight: 1.35,
            }}
          >
            {title}
          </div>
        </div>
        <button className="btn btn-ghost btn-icon" onClick={onClose} style={{ flexShrink: 0 }}>
          <CloseIcon width={16} height={16} />
        </button>
      </div>

      <div style={{ padding: 20, overflowY: "auto", flex: 1 }}>{children}</div>

      {footer && <div style={{ padding: 16, borderTop: "1px solid var(--color-border)" }}>{footer}</div>}
    </div>
  )
}

export function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div
        style={{
          fontSize: 11.5,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          color: "var(--color-text-faint)",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 13.5, color: "var(--color-text)", wordBreak: "break-word", lineHeight: 1.5 }}>
        {value}
      </div>
    </div>
  )
}
