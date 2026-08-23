import type { UploadJobStatus } from "../api/types"

const STATUS_STYLES: Record<UploadJobStatus, { className: string; label: string }> = {
  pending: { className: "badge-neutral", label: "Pending" },
  running: { className: "badge-accent", label: "Running" },
  completed: { className: "badge-success", label: "Completed" },
  completed_with_errors: { className: "badge-warning", label: "Completed with errors" },
  failed: { className: "badge-danger", label: "Failed" },
  cancelled: { className: "badge-neutral", label: "Cancelled" },
}

export function StatusBadge({ status }: { status: UploadJobStatus }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.pending
  return <span className={`badge ${style.className}`}>{style.label}</span>
}
