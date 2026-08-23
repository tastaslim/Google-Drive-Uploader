import { useState } from "react"
import { CloseIcon } from "./icons"

export interface EditResourceValues {
  name?: string
  newParentFolderId?: string
  description?: string
  starred?: boolean
}

interface EditResourceModalProps {
  title: string
  initialName: string
  initialDescription?: string | null
  initialStarred?: boolean | null
  onCancel: () => void
  onSave: (values: EditResourceValues) => Promise<void>
}

export function EditResourceModal({
  title,
  initialName,
  initialDescription,
  initialStarred,
  onCancel,
  onSave,
}: EditResourceModalProps) {
  const [name, setName] = useState(initialName)
  const [newParentFolderId, setNewParentFolderId] = useState("")
  const [description, setDescription] = useState(initialDescription ?? "")
  const [starred, setStarred] = useState(Boolean(initialStarred))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      await onSave({
        name: name !== initialName ? name : undefined,
        newParentFolderId: newParentFolderId.trim() || undefined,
        description: description !== (initialDescription ?? "") ? description : undefined,
        starred: starred !== Boolean(initialStarred) ? starred : undefined,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save changes.")
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className="card modal-panel"
        style={{ width: 440, maxWidth: "90vw" }}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="card-header">
          <h2>{title}</h2>
          <button className="btn btn-ghost btn-icon" onClick={onCancel}>
            <CloseIcon width={14} height={14} />
          </button>
        </div>
        <div className="card-padded">
          {error && <div className="banner banner-error">{error}</div>}

          <div className="field-group">
            <label className="field-label">Name</label>
            <input className="text-input" value={name} onChange={(event) => setName(event.target.value)} />
          </div>

          <div className="field-group">
            <label className="field-label">Move to folder ID (optional)</label>
            <input
              className="text-input mono"
              placeholder="Leave empty to keep current location"
              value={newParentFolderId}
              onChange={(event) => setNewParentFolderId(event.target.value)}
            />
          </div>

          <div className="field-group">
            <label className="field-label">Description</label>
            <input className="text-input" value={description} onChange={(event) => setDescription(event.target.value)} />
          </div>

          <div className="field-group" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              className="checkbox"
              checked={starred}
              onChange={(event) => setStarred(event.target.checked)}
              id="starred-checkbox"
            />
            <label className="field-label" htmlFor="starred-checkbox" style={{ marginBottom: 0 }}>
              Starred
            </label>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
            <button className="btn btn-secondary" onClick={onCancel} disabled={saving}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving || !name.trim()}>
              {saving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
