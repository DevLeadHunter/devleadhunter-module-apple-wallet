import type { LandingStoryActIndex } from '~/types/LandingStoryVisual'

/**
 * Props for {@link LandingWalletStoryVisual} — one act visual of the Apple Wallet
 * story narrative (0 = create, 1 = scan, 2 = stamp, 3 = notify).
 */
export type LandingWalletStoryVisualProps = {
  actIndex: LandingStoryActIndex
}
