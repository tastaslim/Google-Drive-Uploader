import { useEffect, useRef, useState } from "react"
import type { ReactNode } from "react"
import type { NativeAppType } from "../api/types"
import { ChevronRightIcon, FileIcon, FolderIcon, PlusIcon, UploadIcon } from "./icons"

export interface ContextMenuPosition {
  x: number
  y: number
}

interface NativeAppOption {
  appType: NativeAppType
  label: string
  color: string
}

const PRIMARY_APPS: NativeAppOption[] = [
  { appType: "document", label: "Google Docs", color: "#4285f4" },
  { appType: "spreadsheet", label: "Google Sheets", color: "#0f9d58" },
  { appType: "presentation", label: "Google Slides", color: "#f4b400" },
  { appType: "vid", label: "Google Vids", color: "#9c27b0" },
  { appType: "form", label: "Google Forms", color: "#673ab7" },
]

const MORE_APPS: NativeAppOption[] = [
  { appType: "drawing", label: "Google Drawings", color: "#ea4335" },
  { appType: "site", label: "Google Sites", color: "#4285f4" },
  { appType: "script", label: "Apps Script", color: "#4285f4" },
]

function AppSwatch({ color }: { color: string }) {
  return (
    <div
      style={{
        width: 16,
        height: 16,
        borderRadius: 4,
        background: color,
        flexShrink: 0,
      }}
    />
  )
}

interface ContextMenuProps {
  position: ContextMenuPosition
  onClose: () => void
  onNewFolder: () => void
  onFileUpload: () => void
  onFolderUpload: () => void
  onCreateNative: (appType: NativeAppType) => void
}

interface MenuItemProps {
  icon: ReactNode
  label: string
  shortcut?: string
  disabled?: boolean
  onClick?: () => void
  onMouseEnter?: () => void
}

function MenuItem({ icon, label, shortcut, disabled, onClick, onMouseEnter }: MenuItemProps) {
  return (
    <button
      className="context-menu-item"
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
    >
      <span className="context-menu-item-icon">{icon}</span>
      <span className="context-menu-item-label">{label}</span>
      {shortcut && <span className="context-menu-item-shortcut">{shortcut}</span>}
    </button>
  )
}

export function ContextMenu({
  position, onClose, onNewFolder, onFileUpload, onFolderUpload, onCreateNative,
}: ContextMenuProps) {
  const [moreOpen, setMoreOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose()
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose()
    }
    document.addEventListener("mousedown", handleClickOutside)
    document.addEventListener("keydown", handleEscape)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
      document.removeEventListener("keydown", handleEscape)
    }
  }, [onClose])

  const menuWidth = 260
  const viewportWidth = typeof window !== "undefined" ? window.innerWidth : 1200
  const viewportHeight = typeof window !== "undefined" ? window.innerHeight : 800
  const left = Math.min(position.x, viewportWidth - menuWidth - 12)
  const top = Math.min(position.y, viewportHeight - 420)

  return (
    <div
      ref={menuRef}
      className="context-menu"
      style={{ left, top }}
    >
      <MenuItem icon={<PlusIcon width={15} height={15} />} label="New folder" shortcut="⌃ then F" onClick={() => { onNewFolder(); onClose() }} />
      <MenuItem icon={<FileIcon width={15} height={15} />} label="File upload" shortcut="⌃ then U" onClick={() => { onFileUpload(); onClose() }} />
      <MenuItem icon={<FolderIcon width={15} height={15} />} label="Folder upload" shortcut="⌃ then I" onClick={() => { onFolderUpload(); onClose() }} />

      <div className="context-menu-divider" />

      <MenuItem icon={<UploadIcon width={15} height={15} />} label="New project" disabled />

      <div className="context-menu-divider" />

      {PRIMARY_APPS.map((app) => (
        <MenuItem
          key={app.appType}
          icon={<AppSwatch color={app.color} />}
          label={app.label}
          onClick={() => { onCreateNative(app.appType); onClose() }}
          onMouseEnter={() => setMoreOpen(false)}
        />
      ))}

      <div
        className="context-menu-item"
        style={{ position: "relative", cursor: "pointer" }}
        onMouseEnter={() => setMoreOpen(true)}
      >
        <span className="context-menu-item-icon" />
        <span className="context-menu-item-label">More</span>
        <ChevronRightIcon width={13} height={13} style={{ color: "var(--color-text-faint)" }} />

        {moreOpen && (
          <div className="context-menu context-menu-submenu">
            {MORE_APPS.map((app) => (
              <MenuItem
                key={app.appType}
                icon={<AppSwatch color={app.color} />}
                label={app.label}
                onClick={() => { onCreateNative(app.appType); onClose() }}
              />
            ))}
            <div className="context-menu-divider" />
            <MenuItem icon={<PlusIcon width={15} height={15} />} label="Connect more apps" disabled />
          </div>
        )}
      </div>
    </div>
  )
}
