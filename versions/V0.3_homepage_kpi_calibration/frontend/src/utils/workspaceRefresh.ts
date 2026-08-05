export type WorkspaceRefreshSource =
  | 'task-modal'
  | 'review-action'
  | 'smart-upload'
  | 'documents'
  | 'manual'

export type WorkspaceRefreshScope =
  | 'summary'
  | 'tasks'
  | 'reviews'
  | 'documents'
  | 'parse-queue'

export type WorkspaceRefreshPayload = {
  source: WorkspaceRefreshSource
  scopes: WorkspaceRefreshScope[]
  taskId?: string
  reviewId?: string
}

const WORKSPACE_REFRESH_EVENT = 'workspace:data-refresh'

export function emitWorkspaceRefresh(payload: WorkspaceRefreshPayload) {
  window.dispatchEvent(new CustomEvent<WorkspaceRefreshPayload>(WORKSPACE_REFRESH_EVENT, { detail: payload }))
}

export function onWorkspaceRefresh(handler: (payload: WorkspaceRefreshPayload) => void) {
  const listener = (event: Event) => {
    handler((event as CustomEvent<WorkspaceRefreshPayload>).detail)
  }
  window.addEventListener(WORKSPACE_REFRESH_EVENT, listener)
  return () => window.removeEventListener(WORKSPACE_REFRESH_EVENT, listener)
}
