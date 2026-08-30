import QRCode from 'qrcode'

/**
 * Build the public enrollment link and its QR for a program token.
 *
 * The base is the configured public host (e.g. `https://fid.dibodev.fr`) when set, otherwise
 * the current origin's `/carte` route — so QR codes and links work out of the box in dev.
 *
 * @returns Helpers to build the shareable link and its QR data URL.
 */
export function useWalletEnrollLink(): {
  buildLink: (token: string) => string
  buildQr: (token: string) => Promise<string>
} {
  const config: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()

  /**
   * Build the shareable enrollment link for a token.
   * @param token - The program's public token.
   * @returns The absolute enrollment URL.
   */
  function buildLink(token: string): string {
    const configured: string = config.public.walletEnrollBase
    const base: string = configured || (import.meta.client ? `${window.location.origin}/carte` : '/carte')
    return `${base}/${token}`
  }

  /**
   * Render the enrollment link as a QR-code data URL.
   * @param token - The program's public token.
   * @returns A PNG data URL of the QR code.
   */
  async function buildQr(token: string): Promise<string> {
    return QRCode.toDataURL(buildLink(token), { margin: 1, width: 512 })
  }

  return { buildLink, buildQr }
}
