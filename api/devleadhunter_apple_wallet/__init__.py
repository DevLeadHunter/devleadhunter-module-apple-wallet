"""
Apple Wallet loyalty cards, an optional product module of DevLeadHunter.

A merchant gets a stamp card his customers add to Apple Wallet in one scan, stamps it at the counter and pushes his
offers to their lock screen; the operator sells it as a monthly Stripe subscription. The core discovers the module
through the ``devleadhunter.product_modules`` entry point (:class:`devleadhunter_apple_wallet.module.AppleWalletModule`)
and imports nothing from it directly.
"""
