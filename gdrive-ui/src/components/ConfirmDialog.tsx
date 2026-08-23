interface ConfirmDialogProps {
  title: string
  message: string
  confirmLabel?: string
  destructive?: boolean
  busy?: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  destructive = true,
  busy = false,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="card modal-panel" style={{ width: 400, maxWidth: "90vw" }} onClick={(event) => event.stopPropagation()}>
        <div className="card-padded">
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>{title}</div>
          <div style={{ fontSize: 14, color: "var(--color-text-muted)", marginBottom: 20 }}>{message}</div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            <button className="btn btn-secondary" onClick={onCancel} disabled={busy}>
              Cancel
            </button>
            <button className={destructive ? "btn btn-danger" : "btn btn-primary"} onClick={onConfirm} disabled={busy}>
              {busy ? "Working..." : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
