import type { FileGlyph } from "../utils/fileType"

interface FileTypeIconProps {
  color: string
  glyph: FileGlyph
  size?: number
}

/**
 * Drive-style "sheet with folded corner" filled solid with the category
 * color, plus a bold vector pictogram (not text) identifying the sub-type —
 * lines/bars for docs, a grid for sheets, a play triangle for video, a
 * waveform for audio, etc. Pure SVG paths, so it stays crisp at any size.
 */
export function FileTypeIcon({ color, glyph, size = 32 }: FileTypeIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M8 2h11l7 7v19a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z" fill={color} />
      <path d="M19 2v5.5A1.5 1.5 0 0 0 20.5 9H26" fill="#ffffff" fillOpacity={0.32} />
      <Pictogram glyph={glyph} />
    </svg>
  )
}

function Pictogram({ glyph }: { glyph: FileGlyph }) {
  switch (glyph) {
    case "letter-pdf":
      return (
        <text x={16} y={23.5} textAnchor="middle" fontSize={9} fontWeight={800} fontFamily="Arial, Helvetica, sans-serif" fill="#fff">
          PDF
        </text>
      )
    case "letter-doc":
      return (
        <g stroke="#fff" strokeWidth={2} strokeLinecap="round">
          <line x1={11} y1={16} x2={21} y2={16} />
          <line x1={11} y1={20} x2={21} y2={20} />
          <line x1={11} y1={24} x2={17} y2={24} />
        </g>
      )
    case "letter-sheet":
      return (
        <g stroke="#fff" strokeWidth={1.8}>
          <rect x={10.5} y={13.5} width={11} height={11} rx={1} />
          <line x1={10.5} y1={17.6} x2={21.5} y2={17.6} />
          <line x1={10.5} y1={21.7} x2={21.5} y2={21.7} />
          <line x1={16} y1={13.5} x2={16} y2={24.5} />
        </g>
      )
    case "letter-slide":
      return (
        <g>
          <rect x={9.5} y={14} width={13} height={9.5} rx={1.1} fill="none" stroke="#fff" strokeWidth={1.8} />
          <path d="M12.5 21.3 15.7 17.5 17.8 19.7 20.3 16.4 22 21.3Z" fill="none" stroke="#fff" strokeWidth={1.4} strokeLinejoin="round" strokeLinecap="round" />
        </g>
      )
    case "letter-ebook":
      return (
        <g stroke="#fff" strokeWidth={1.8} strokeLinejoin="round">
          <path d="M16 15.5c-1.6-1.3-3.8-1.5-5.5-.8v9c1.7-.7 3.9-.5 5.5.8 1.6-1.3 3.8-1.5 5.5-.8v-9c-1.7-.7-3.9-.5-5.5.8Z" />
          <line x1={16} y1={15.5} x2={16} y2={24.5} />
        </g>
      )
    case "text":
      return (
        <g stroke="#fff" strokeWidth={2} strokeLinecap="round">
          <line x1={11} y1={15} x2={21} y2={15} />
          <line x1={11} y1={19} x2={21} y2={19} />
          <line x1={11} y1={23} x2={18} y2={23} />
        </g>
      )
    case "data":
      return (
        <text x={16} y={23.5} textAnchor="middle" fontSize={11} fontWeight={700} fontFamily="Consolas, monospace" fill="#fff">
          {"{ }"}
        </text>
      )
    case "database":
      return (
        <g stroke="#fff" strokeWidth={1.8}>
          <ellipse cx={16} cy={14.8} rx={5.2} ry={1.9} />
          <path d="M10.8 14.8v8c0 1.05 2.3 1.9 5.2 1.9s5.2-.85 5.2-1.9v-8" />
          <path d="M10.8 18.8c0 1.05 2.3 1.9 5.2 1.9s5.2-.85 5.2-1.9" />
        </g>
      )
    case "image":
      return (
        <g>
          <rect x={9.5} y={13.5} width={13} height={10} rx={1.1} fill="none" stroke="#fff" strokeWidth={1.8} />
          <circle cx={12.7} cy={16.6} r={1.15} fill="#fff" />
          <path d="M10 22.3 13.6 18.4 16 20.9 19.2 17 22.5 22.3" fill="none" stroke="#fff" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      )
    case "video":
      return (
        <g>
          <circle cx={16} cy={18.5} r={6.3} fill="none" stroke="#fff" strokeWidth={1.8} />
          <path d="M14.3 15.6v5.8l5-2.9Z" fill="#fff" />
        </g>
      )
    case "audio":
      return (
        <g stroke="#fff" strokeWidth={1.9} strokeLinecap="round">
          <line x1={11.5} y1={19.5} x2={11.5} y2={22} />
          <line x1={14.2} y1={16.5} x2={14.2} y2={24.5} />
          <line x1={16.9} y1={18} x2={16.9} y2={23} />
          <line x1={19.6} y1={14.8} x2={19.6} y2={26} />
          <line x1={22.3} y1={17.3} x2={22.3} y2={22.5} />
        </g>
      )
    case "archive":
      return (
        <g stroke="#fff" strokeWidth={1.8}>
          <rect x={12.5} y={13.5} width={7} height={11} rx={1} />
          <line x1={16} y1={13.5} x2={16} y2={15.5} />
          <line x1={14.5} y1={16.3} x2={17.5} y2={16.3} />
          <line x1={14.5} y1={18.1} x2={17.5} y2={18.1} />
          <line x1={14.5} y1={19.9} x2={17.5} y2={19.9} />
          <circle cx={16} cy={22.2} r={1} />
        </g>
      )
    case "email":
      return (
        <g stroke="#fff" strokeWidth={1.8} strokeLinejoin="round">
          <rect x={9.5} y={15} width={13} height={9} rx={1.1} />
          <path d="M10 15.7 16 20.1 22 15.7" />
        </g>
      )
    case "calendar":
      return (
        <g stroke="#fff" strokeWidth={1.8} strokeLinejoin="round">
          <rect x={9.5} y={14} width={13} height={10.5} rx={1.2} />
          <line x1={9.5} y1={17.3} x2={22.5} y2={17.3} />
          <line x1={12.5} y1={12.3} x2={12.5} y2={15} />
          <line x1={19.5} y1={12.3} x2={19.5} y2={15} />
        </g>
      )
    case "font":
      return (
        <text x={16} y={24} textAnchor="middle" fontSize={13} fontWeight={800} fontFamily="Georgia, serif" fill="#fff">
          A
        </text>
      )
    case "certificate":
      return (
        <path
          d="M16 13.3 21 15.1v4c0 3-2.1 5.6-5 6.6-2.9-1-5-3.6-5-6.6v-4Z"
          fill="none"
          stroke="#fff"
          strokeWidth={1.8}
          strokeLinejoin="round"
        />
      )
    case "code":
      return (
        <text x={16} y={23} textAnchor="middle" fontSize={9} fontWeight={700} fontFamily="Consolas, monospace" fill="#fff">
          {"</>"}
        </text>
      )
    default:
      return null
  }
}
