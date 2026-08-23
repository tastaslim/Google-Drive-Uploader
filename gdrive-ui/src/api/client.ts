import type {
  BulkDeleteResponse,
  CreateFolderRequest,
  CreateNativeFileRequest,
  DeleteFilesRequest,
  DeleteResult,
  FileResource,
  FolderSearchResponse,
  FolderStatsResponse,
  FolderUploadResult,
  PaginatedFilesResponse,
  PaginatedSharedDrivesResponse,
  SupportedFormatsResponse,
  UpdateFileRequest,
  UpdateFolderRequest,
  UploadFilesRequest,
  UploadJobResponse,
} from "./types"

export const apiBaseUrl: string = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

async function request<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as TResponse
  }
  return (await response.json()) as TResponse
}

async function requestMultipart<TResponse>(path: string, formData: FormData): Promise<TResponse> {
  // No Content-Type header here on purpose — the browser sets
  // multipart/form-data with the correct boundary itself; overriding it
  // (as the JSON `request` helper does) breaks the upload.
  const response = await fetch(`${apiBaseUrl}${path}`, { method: "POST", body: formData })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, detail)
  }
  return (await response.json()) as TResponse
}

function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value))
    }
  }
  const query = searchParams.toString()
  return query ? `?${query}` : ""
}

export const uploadsApi = {
  create: (body: UploadFilesRequest) =>
    request<UploadJobResponse>("/uploads", { method: "POST", body: JSON.stringify(body) }),

  get: (jobId: string) => request<UploadJobResponse>(`/uploads/${jobId}`),

  list: () => request<UploadJobResponse[]>("/uploads"),

  cancel: (jobId: string) => request<UploadJobResponse>(`/uploads/${jobId}/cancel`, { method: "POST" }),

  getFormats: () => request<SupportedFormatsResponse>("/uploads/formats"),
}

export const filesApi = {
  list: (params: {
    sharedDriveIdOrUrl: string
    folderId?: string
    pageSize?: number
    pageToken?: string
    includeFolders?: boolean
  }) =>
    request<PaginatedFilesResponse>(
      `/files${buildQuery({
        sharedDriveIdOrUrl: params.sharedDriveIdOrUrl,
        folderId: params.folderId,
        pageSize: params.pageSize,
        pageToken: params.pageToken,
        includeFolders: params.includeFolders,
      })}`,
    ),

  get: (fileId: string, sharedDriveIdOrUrl: string) =>
    request<FileResource>(`/files/${fileId}${buildQuery({ sharedDriveIdOrUrl })}`),

  uploadReal: (file: File, sharedDriveIdOrUrl: string, folderId: string | undefined) => {
    const formData = new FormData()
    formData.set("sharedDriveIdOrUrl", sharedDriveIdOrUrl)
    if (folderId) formData.set("folderId", folderId)
    formData.set("file", file)
    return requestMultipart<FileResource>("/files/upload", formData)
  },

  createNative: (body: CreateNativeFileRequest) =>
    request<FileResource>("/files/native", { method: "POST", body: JSON.stringify(body) }),

  downloadUrl: (fileId: string, sharedDriveIdOrUrl: string) =>
    `${apiBaseUrl}/files/${fileId}/download${buildQuery({ sharedDriveIdOrUrl })}`,

  update: (fileId: string, body: UpdateFileRequest) =>
    request<FileResource>(`/files/${fileId}`, { method: "PATCH", body: JSON.stringify(body) }),

  remove: (fileId: string, sharedDriveIdOrUrl: string, permanent: boolean) =>
    request<DeleteResult>(`/files/${fileId}${buildQuery({ sharedDriveIdOrUrl, permanent })}`, {
      method: "DELETE",
    }),

  removeBatch: (body: DeleteFilesRequest) =>
    request<BulkDeleteResponse>("/files/delete-batch", { method: "POST", body: JSON.stringify(body) }),
}

export const foldersApi = {
  create: (body: CreateFolderRequest) =>
    request<FileResource>("/folders", { method: "POST", body: JSON.stringify(body) }),

  uploadBatch: (
    filesWithPaths: { file: File; relativePath: string }[],
    sharedDriveIdOrUrl: string,
    parentFolderId: string | undefined,
  ) => {
    const formData = new FormData()
    formData.set("sharedDriveIdOrUrl", sharedDriveIdOrUrl)
    if (parentFolderId) formData.set("parentFolderId", parentFolderId)
    for (const { file, relativePath } of filesWithPaths) {
      formData.append("relativePaths", relativePath)
      formData.append("files", file)
    }
    return requestMultipart<FolderUploadResult>("/folders/upload-batch", formData)
  },

  list: (params: { sharedDriveIdOrUrl: string; parentFolderId?: string; pageSize?: number; pageToken?: string }) =>
    request<PaginatedFilesResponse>(
      `/folders${buildQuery({
        sharedDriveIdOrUrl: params.sharedDriveIdOrUrl,
        parentFolderId: params.parentFolderId,
        pageSize: params.pageSize,
        pageToken: params.pageToken,
      })}`,
    ),

  get: (folderId: string, sharedDriveIdOrUrl: string) =>
    request<FileResource>(`/folders/${folderId}${buildQuery({ sharedDriveIdOrUrl })}`),

  search: (params: { sharedDriveIdOrUrl: string; query: string; pageSize?: number; pageToken?: string }) =>
    request<FolderSearchResponse>(
      `/folders/search${buildQuery({
        sharedDriveIdOrUrl: params.sharedDriveIdOrUrl,
        query: params.query,
        pageSize: params.pageSize,
        pageToken: params.pageToken,
      })}`,
    ),

  downloadUrl: (folderId: string, sharedDriveIdOrUrl: string) =>
    `${apiBaseUrl}/folders/${folderId}/download${buildQuery({ sharedDriveIdOrUrl })}`,

  stats: (folderId: string, sharedDriveIdOrUrl: string) =>
    request<FolderStatsResponse>(`/folders/${folderId}/stats${buildQuery({ sharedDriveIdOrUrl })}`),

  update: (folderId: string, body: UpdateFolderRequest) =>
    request<FileResource>(`/folders/${folderId}`, { method: "PATCH", body: JSON.stringify(body) }),

  remove: (folderId: string, sharedDriveIdOrUrl: string, permanent: boolean) =>
    request<DeleteResult>(`/folders/${folderId}${buildQuery({ sharedDriveIdOrUrl, permanent })}`, {
      method: "DELETE",
    }),
}

export const drivesApi = {
  list: (params?: { pageSize?: number; pageToken?: string }) =>
    request<PaginatedSharedDrivesResponse>(
      `/drives${buildQuery({ pageSize: params?.pageSize, pageToken: params?.pageToken })}`,
    ),
}

export const trashApi = {
  list: (params: { sharedDriveIdOrUrl: string; pageSize?: number; pageToken?: string }) =>
    request<PaginatedFilesResponse>(
      `/trash${buildQuery({
        sharedDriveIdOrUrl: params.sharedDriveIdOrUrl,
        pageSize: params.pageSize,
        pageToken: params.pageToken,
      })}`,
    ),

  restore: (fileId: string, sharedDriveIdOrUrl: string) =>
    request<FileResource>(`/trash/${fileId}/restore${buildQuery({ sharedDriveIdOrUrl })}`, {
      method: "POST",
    }),

  permanentlyDelete: (fileId: string, sharedDriveIdOrUrl: string) =>
    request<DeleteResult>(`/trash/${fileId}${buildQuery({ sharedDriveIdOrUrl })}`, {
      method: "DELETE",
    }),
}
