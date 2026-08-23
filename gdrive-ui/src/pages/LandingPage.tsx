import { Link } from "react-router-dom"
import {
  ArrowLeftIcon,
  FileIcon,
  FolderIcon,
  HardDriveIcon,
  RefreshIcon,
  UploadIcon,
} from "../components/icons"

const FEATURES = [
  {
    icon: UploadIcon,
    title: "Bulk synthetic uploads",
    description:
      "Generate and stream files across 90+ formats — from documents and images to multi-gigabyte binaries — straight into a folder, with size distributions you control.",
  },
  {
    icon: HardDriveIcon,
    title: "Every format that matters",
    description:
      "Office documents, PDFs, media, code, archives, and raw binaries up to 5GB, streamed without ever holding a full file in memory.",
  },
  {
    icon: FolderIcon,
    title: "Browse like Google Drive",
    description:
      "Files and folders together in one view, breadcrumb navigation, infinite scroll, and full metadata on every item — no separate tabs to hunt through.",
  },
  {
    icon: FileIcon,
    title: "Full file & folder control",
    description:
      "Rename, move, star, and delete individual items or entire selections. Download single files or an entire folder tree as a zip.",
  },
]

const STEPS = [
  { number: "01", title: "Connect a Shared Drive", description: "Pick from every Shared Drive your Google identity can access." },
  { number: "02", title: "Upload or browse", description: "Start a bulk upload job, or browse existing files and folders like you would in Drive itself." },
  { number: "03", title: "Manage with confidence", description: "Rename, move, star, delete, and download — all backed by a real FastAPI service, not a toy." },
]

export function LandingPage() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "20px 44px",
          maxWidth: 1180,
          margin: "0 auto",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="sidebar-brand-mark">
            <HardDriveIcon width={16} height={16} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 15.5, letterSpacing: "-0.01em" }}>Drive Loader</span>
        </div>
        <Link to="/drives" className="btn btn-secondary btn-sm">
          Go to drives
          <ArrowLeftIcon width={13} height={13} style={{ transform: "rotate(180deg)" }} />
        </Link>
      </header>

      <section style={{ maxWidth: 780, margin: "0 auto", padding: "72px 24px 56px", textAlign: "center" }}>
        <div className="badge badge-accent" style={{ marginBottom: 20 }}>
          <span className="badge-dot" />
          Backed by a real Google Shared Drive API
        </div>
        <h1
          style={{
            fontSize: 44,
            fontWeight: 750,
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            margin: "0 0 18px",
          }}
        >
          Your whole Shared Drive,
          <br />
          <span style={{ backgroundImage: "var(--gradient-brand)", WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>
            one workspace away.
          </span>
        </h1>
        <p
          style={{
            fontSize: 17,
            color: "var(--color-text-muted)",
            lineHeight: 1.6,
            maxWidth: 560,
            margin: "0 auto 32px",
          }}
        >
          Upload thousands of test files in any format, then browse, organize, and manage every
          drive you have access to — with an interface that feels like Google Drive itself.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
          <Link to="/drives" className="btn btn-primary" style={{ padding: "12px 24px", fontSize: 15 }}>
            <HardDriveIcon width={16} height={16} />
            Browse your drives
          </Link>
        </div>
      </section>

      <section style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px 80px" }}>
        <div className="drive-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
          {FEATURES.map((feature) => (
            <div key={feature.title} className="card card-padded">
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: "var(--color-accent-soft)",
                  color: "var(--color-accent)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 16,
                }}
              >
                <feature.icon width={19} height={19} />
              </div>
              <div style={{ fontWeight: 650, fontSize: 15, marginBottom: 8 }}>{feature.title}</div>
              <div style={{ fontSize: 13.5, color: "var(--color-text-muted)", lineHeight: 1.55 }}>
                {feature.description}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section style={{ background: "var(--color-surface)", borderTop: "1px solid var(--color-border)", borderBottom: "1px solid var(--color-border)" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "64px 24px" }}>
          <h2 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", textAlign: "center", margin: "0 0 44px" }}>
            How it works
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 32 }}>
            {STEPS.map((step) => (
              <div key={step.number}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: "var(--color-accent)",
                    fontFamily: "var(--font-mono)",
                    marginBottom: 10,
                  }}
                >
                  {step.number}
                </div>
                <div style={{ fontWeight: 650, fontSize: 15.5, marginBottom: 8 }}>{step.title}</div>
                <div style={{ fontSize: 13.5, color: "var(--color-text-muted)", lineHeight: 1.55 }}>
                  {step.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ maxWidth: 640, margin: "0 auto", padding: "72px 24px", textAlign: "center" }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", margin: "0 0 12px" }}>
          Ready to get started?
        </h2>
        <p style={{ fontSize: 14.5, color: "var(--color-text-muted)", marginBottom: 28 }}>
          Connect to any Shared Drive your Google identity can access — no setup beyond that.
        </p>
        <Link to="/drives" className="btn btn-primary" style={{ padding: "12px 24px", fontSize: 15 }}>
          <RefreshIcon width={16} height={16} />
          View my Shared Drives
        </Link>
      </section>

      <footer style={{ borderTop: "1px solid var(--color-border)", padding: "24px 44px", textAlign: "center" }}>
        <span style={{ fontSize: 12.5, color: "var(--color-text-faint)" }}>
          Drive Loader — Google Shared Drive Service
        </span>
      </footer>
    </div>
  )
}
