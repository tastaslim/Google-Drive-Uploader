export interface UploadFilesRequest {
  count: number
  sharedDriveIdOrUrl: string
  folderId?: string | null
  averageFileSizeBytes?: number
  excludedExtensions?: string[]
}

export interface UploadJobError {
  fileIndex: number
  fileName: string
  errorMessage: string
}

export type UploadJobEventStatus = "generated" | "uploading" | "uploaded" | "failed"

export interface UploadJobEvent {
  fileIndex: number
  fileName: string
  extension: string
  sizeBytes: number | null
  status: UploadJobEventStatus
  timestamp: number
}

export type UploadJobStatus =
  | "pending"
  | "running"
  | "completed"
  | "completed_with_errors"
  | "failed"
  | "cancelled"

export interface UploadJobResponse {
  jobId: string
  sharedDriveId: string
  destinationFolderId: string
  requestedCount: number
  averageFileSizeBytes: number
  excludedExtensions: string[]
  smallFileCount: number
  largeFileCountsByBucket: Record<string, number>
  status: UploadJobStatus
  uploadedCount: number
  failedCount: number
  remainingCount: number
  createdAt: number
  startedAt: number | null
  finishedAt: number | null
  elapsedSeconds: number | null
  errors: UploadJobError[]
  recentEvents: UploadJobEvent[]
}

export interface SupportedFormatsResponse {
  extensions: string[]
}

export interface FolderUploadResultItem {
  relativePath: string
  success: boolean
  fileId?: string | null
  errorMessage?: string | null
}

export interface FolderUploadResult {
  results: FolderUploadResultItem[]
}

export type NativeAppType =
  | "document"
  | "spreadsheet"
  | "presentation"
  | "vid"
  | "form"
  | "drawing"
  | "site"
  | "script"

export interface CreateNativeFileRequest {
  sharedDriveIdOrUrl: string
  appType: NativeAppType
  name?: string
  folderId?: string | null
}

export interface FileResource {
  id: string
  name: string
  mimeType: string
  parents?: string[] | null
  driveId?: string | null
  size?: string | null
  createdTime?: string | null
  modifiedTime?: string | null
  trashed?: boolean | null
  md5Checksum?: string | null
  webViewLink?: string | null
  starred?: boolean | null
  description?: string | null
}

export interface PaginatedFilesResponse {
  files: FileResource[]
  nextPageToken?: string | null
}

export interface FolderSearchResultItem {
  id: string
  name: string
  path: string
  createdTime?: string | null
  modifiedTime?: string | null
}

export interface FolderSearchResponse {
  folders: FolderSearchResultItem[]
  nextPageToken?: string | null
}

export interface FolderStatsResponse {
  folderId: string
  fileCount: number
  folderCount: number
  totalSizeBytes: number
}

export interface CreateFolderRequest {
  sharedDriveIdOrUrl: string
  name: string
  parentFolderId?: string | null
  description?: string | null
}

export interface UpdateFolderRequest {
  sharedDriveIdOrUrl: string
  name?: string | null
  newParentFolderId?: string | null
  description?: string | null
  starred?: boolean | null
}

export interface UpdateFileRequest {
  sharedDriveIdOrUrl: string
  name?: string | null
  newParentFolderId?: string | null
  description?: string | null
  starred?: boolean | null
}

export interface DeleteFilesRequest {
  sharedDriveIdOrUrl: string
  fileIds: string[]
  permanent?: boolean
}

export interface DeleteResult {
  fileId: string
  success: boolean
  errorMessage?: string | null
}

export interface BulkDeleteResponse {
  results: DeleteResult[]
}

export interface SharedDriveResource {
  id: string
  name: string
  createdTime?: string | null
}

export interface PaginatedSharedDrivesResponse {
  drives: SharedDriveResource[]
  nextPageToken?: string | null
}
