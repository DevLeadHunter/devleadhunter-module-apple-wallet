/**
 * Props for {@link LandingTradesTicker} — the infinite « trade · city » marquee.
 * The i18n namespace must expose `ariaLabel` and `item1..itemN` keys.
 */
export type LandingTradesTickerProps = {
  keyPrefix: string
  itemCount: number
}
