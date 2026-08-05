/** V0.4 governance API contracts (rectification tasks / special plans). */

export type RectificationTask = {
  id: number
  taskCode: string
  title: string
  responsibleOrgId?: number | null
  deadline?: string | null
  taskStatus: string
  dataNature?: string | null
  isDemo?: boolean
  effectiveStatus?: string | null
  effectiveAt?: string | null
  effectiveBy?: number | null
  rectificationCompletedDate: string | null
  rectificationCompletedBy: number | null
  createdAt?: string | null
  updatedAt?: string | null
}

export type RectificationTaskList = {
  total: number
  items: RectificationTask[]
}

export type RectificationTaskPatch = {
  rectificationCompletedDate?: string | null
  rectificationCompletedBy?: number | null
}

export type SpecialPlanApprovalFile = {
  id: number
  fileCode?: string | null
  originalName?: string | null
  fileExt?: string | null
  mimeType?: string | null
  fileSize?: number | null
  uploadTime?: string | null
  parseStatus?: string | null
}

export type SpecialPlanApproval = {
  id: number
  projectId: number
  riskPointId: number
  planCode: string
  planName: string
  riskLevel: string
  approvalStatus: string
  approvalDate?: string | null
  approvalFileId?: number | null
  approvalFile?: SpecialPlanApprovalFile | null
  sourceDocRef?: string | null
  dataNature?: string | null
  isDemo?: boolean
  createdAt?: string | null
  updatedAt?: string | null
}

export type SpecialPlanList = {
  total: number
  items: SpecialPlanApproval[]
}

export type SpecialPlanCreatePayload = {
  projectId: number
  riskPointId: number
  planCode: string
  planName: string
  riskLevel: string
  approvalStatus: string
  approvalDate?: string | null
  approvalFileId?: number | null
  sourceDocRef?: string | null
  dataNature?: string
  isDemo?: boolean
}

export type SpecialPlanPatchPayload = {
  planName?: string
  riskLevel?: string
  approvalStatus?: string
  approvalDate?: string | null
  approvalFileId?: number | null
  sourceDocRef?: string | null
}

export type ApiMutationResult<T> =
  | { ok: true; data: T; status: number; message?: string }
  | { ok: false; data: null; status: number; message: string }
