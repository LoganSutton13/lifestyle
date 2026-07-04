export class ApiError extends Error {
  code: string
  details: Record<string, unknown>

  constructor(message: string, code = 'UNKNOWN_ERROR', details: Record<string, unknown> = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
  }
}

export interface ErrorPayload {
  error?: {
    code?: string
    message?: string
    details?: Record<string, unknown>
  }
}

export async function parseApiError(response: Response): Promise<ApiError> {
  try {
    const data = (await response.json()) as ErrorPayload
    const message = data.error?.message ?? response.statusText ?? 'Request failed'
    const code = data.error?.code ?? 'HTTP_ERROR'
    const details = data.error?.details ?? {}
    return new ApiError(message, code, details)
  } catch {
    return new ApiError(response.statusText || 'Request failed', 'HTTP_ERROR')
  }
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong'
}
