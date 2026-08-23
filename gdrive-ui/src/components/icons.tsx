import type { SVGProps } from "react"

function Icon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    />
  )
}

export const UploadIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 3v12" />
    <path d="m7 8 5-5 5 5" />
    <path d="M5 21h14" />
  </Icon>
)

export const FileIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M14 3v5a1 1 0 0 0 1 1h5" />
    <path d="M6 3h8l6 6v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
  </Icon>
)

export const FolderIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
  </Icon>
)

export const TrashIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M3 6h18" />
    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
    <path d="M10 11v6" />
    <path d="M14 11v6" />
  </Icon>
)

export const EditIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 20h9" />
    <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
  </Icon>
)

export const DownloadIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 3v12" />
    <path d="m7 12 5 5 5-5" />
    <path d="M5 21h14" />
  </Icon>
)

export const StarIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 2 15 9l7 1-5 5 1.5 7-6.5-3.5L5 22l1.5-7-5-5 7-1Z" />
  </Icon>
)

export const RefreshIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M21 12a9 9 0 1 1-2.64-6.36" />
    <path d="M21 3v6h-6" />
  </Icon>
)

export const ChevronRightIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="m9 18 6-6-6-6" />
  </Icon>
)

export const PlusIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </Icon>
)

export const CloseIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </Icon>
)

export const HardDriveIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="m5 10 3-7h8l3 7" />
    <rect x="2" y="10" width="20" height="8" rx="2" />
    <circle cx="6.5" cy="14" r="0.6" fill="currentColor" stroke="none" />
    <path d="M10 14h4" />
  </Icon>
)

export const ArrowLeftIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M19 12H5" />
    <path d="m12 19-7-7 7-7" />
  </Icon>
)

export const AlertIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
    <path d="M12 9v4" />
    <path d="M12 17h.01" />
  </Icon>
)

export const RestoreIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
    <path d="M3 3v5h5" />
  </Icon>
)

export const SunIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2" />
    <path d="M12 20v2" />
    <path d="m4.93 4.93 1.41 1.41" />
    <path d="m17.66 17.66 1.41 1.41" />
    <path d="M2 12h2" />
    <path d="M20 12h2" />
    <path d="m6.34 17.66-1.41 1.41" />
    <path d="m19.07 4.93-1.41 1.41" />
  </Icon>
)

export const MoonIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
  </Icon>
)
