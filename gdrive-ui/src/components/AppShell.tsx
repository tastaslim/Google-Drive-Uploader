import type { ReactNode } from "react"
import { useEffect, useState } from "react"
import { Link, NavLink, useParams } from "react-router-dom"
import { ArrowLeftIcon, FolderIcon, HardDriveIcon, MoonIcon, SunIcon, TrashIcon, UploadIcon } from "./icons"
import { useDriveName } from "../hooks/useDriveName"

interface AppShellProps {
  children: ReactNode
}

type Theme = "light" | "dark"

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light"
  const stored = window.localStorage.getItem("theme")
  if (stored === "light" || stored === "dark") return stored
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme)
    window.localStorage.setItem("theme", theme)
  }, [theme])

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
      title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      aria-label="Toggle color theme"
    >
      {theme === "dark" ? <SunIcon width={14} height={14} /> : <MoonIcon width={14} height={14} />}
    </button>
  )
}

function DriveScopedNav({ driveId }: { driveId: string }) {
  const driveName = useDriveName(driveId)

  return (
    <>
      <Link to="/drives" className="sidebar-drive-pill">
        <ArrowLeftIcon width={13} height={13} style={{ flexShrink: 0 }} />
        <span className="sidebar-drive-pill-name">{driveName ?? "Loading…"}</span>
      </Link>
      <nav className="sidebar-nav">
        <NavLink
          to={`/drives/${driveId}/browse`}
          className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
        >
          <FolderIcon width={16} height={16} />
          Browse
        </NavLink>
        <NavLink
          to={`/drives/${driveId}/generate`}
          className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
        >
          <UploadIcon width={16} height={16} />
          Generate &amp; Upload
        </NavLink>
        <NavLink
          to={`/drives/${driveId}/trash`}
          className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
        >
          <TrashIcon width={16} height={16} />
          Trash
        </NavLink>
      </nav>
    </>
  )
}

export function AppShell({ children }: AppShellProps) {
  const { driveId } = useParams<{ driveId: string }>()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/drives" className="sidebar-brand">
          <div className="sidebar-brand-mark">
            <HardDriveIcon width={16} height={16} />
          </div>
          <div className="sidebar-brand-name">Drive Loader</div>
        </Link>
        {driveId && <DriveScopedNav driveId={driveId} />}
        <div className="sidebar-footer">
          <span>Google Shared Drive Service</span>
          <ThemeToggle />
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  )
}
