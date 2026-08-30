import { ApiClient } from './api'
import type {
  WalletMerchantCredentials,
  WalletProgram,
  WalletProgramCreatePayload,
  WalletProgramUpdatePayload,
} from '~/types/WalletProgram'

/** Operator-side loyalty program configuration + merchant login provisioning. */
export class WalletProgramService {
  /**
   * List the operator's loyalty programs, most recent first.
   * @returns The programs.
   */
  static list(): Promise<WalletProgram[]> {
    return ApiClient.get<WalletProgram[]>('/api/v1/wallet/programs')
  }

  /**
   * Fetch one program.
   * @param programId - The program to fetch.
   * @returns The program.
   */
  static get(programId: number): Promise<WalletProgram> {
    return ApiClient.get<WalletProgram>(`/api/v1/wallet/programs/${programId}`)
  }

  /**
   * Create a program (starts as a draft with a public enrollment token).
   * @param payload - The program configuration.
   * @returns The created program.
   */
  static create(payload: WalletProgramCreatePayload): Promise<WalletProgram> {
    return ApiClient.post<WalletProgram>('/api/v1/wallet/programs', payload)
  }

  /**
   * Edit a program.
   * @param programId - The program to edit.
   * @param payload - The fields to change.
   * @returns The updated program.
   */
  static update(programId: number, payload: WalletProgramUpdatePayload): Promise<WalletProgram> {
    return ApiClient.patch<WalletProgram>(`/api/v1/wallet/programs/${programId}`, payload)
  }

  /**
   * Provision (or reset) the merchant login for a program.
   * @param programId - The program whose login to provision.
   * @returns The credentials, to hand over once.
   */
  static provisionLogin(programId: number): Promise<WalletMerchantCredentials> {
    return ApiClient.post<WalletMerchantCredentials>(`/api/v1/wallet/merchant/${programId}/login-credentials`, {})
  }
}
