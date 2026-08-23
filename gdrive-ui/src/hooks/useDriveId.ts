import { useParams } from "react-router-dom"

/** Reads the active Shared Drive ID from the /drives/:driveId/* route param. */
export function useDriveId(): string {
  const { driveId } = useParams<{ driveId: string }>()
  if (!driveId) {
    throw new Error("useDriveId must be used within a /drives/:driveId/* route")
  }
  return driveId
}
