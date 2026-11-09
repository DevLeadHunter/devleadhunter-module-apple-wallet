"""The Apple Wallet module as the core sees it, through the ``devleadhunter.product_modules`` entry point.

Everything the hooks hand over is imported here, when the registry loads the module: the registry catches a module
that fails to import and runs without it, whereas a hook failing later (while the core mounts its routes) would take
the core down.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from core.product_modules.contract import BackgroundLoop, ProductModule

from devleadhunter_apple_wallet.campaigns.email_templates import LOYALTY_CARD_EMAIL_TEMPLATES
from devleadhunter_apple_wallet.campaigns.loyalty_card_offer import LoyaltyCardOffer
from devleadhunter_apple_wallet.routes import merchant, wallet, wallet_merchant, wallet_programs
from devleadhunter_apple_wallet.services.wallet_automation_service import wallet_automation_worker
from devleadhunter_apple_wallet.services.wallet_subscription_service import wallet_subscription_service

if TYPE_CHECKING:
    from fastapi import APIRouter
    from sqlalchemy.orm import Session

    from core.product_modules.campaign_offer import CampaignOffer

_MIGRATIONS_PACKAGE: str = "devleadhunter_apple_wallet.migrations"


class AppleWalletModule(ProductModule):
    """
    Apple Wallet loyalty cards: a merchant's stamp card in his customers' iPhones, sold as a monthly subscription.

    Installed in production switched off (``enabled_by_default``): its routes answer 404 and its worker stays stopped
    until the super admin switches it on; its Stripe subscription events are handled either way.
    """

    key: ClassVar[str] = "apple-wallet"
    label: ClassVar[str] = "Cartes Apple Wallet"
    description: ClassVar[str] = (
        "Cartes de fidélité à tampons dans Apple Wallet pour les commerçants : programme, tampons, offres sur l'écran "
        "verrouillé, espace commerçant et abonnement mensuel."
    )
    enabled_by_default: ClassVar[bool] = False

    # Tracked by name in schema_migrations: a name never changes (add_loyalty_card_email_templates ran in prod).
    MIGRATION_NAMES: ClassVar[tuple[str, ...]] = (
        "add_wallet_loyalty_tables",
        "add_wallet_credentials_table",
        "add_loyalty_program_public_token",
        "add_loyalty_card_current_offer",
        "add_wallet_automation_jobs",
        "add_wallet_subscriptions",
        "add_merchant_accounts",
        "add_loyalty_card_email_templates",
    )

    def __init__(self) -> None:
        self._campaign_offer: LoyaltyCardOffer = LoyaltyCardOffer()

    def load(self) -> None:
        """Register the module's tables on the core's metadata, before ``init_db()`` creates the missing ones."""
        import devleadhunter_apple_wallet.models  # noqa: F401

    def routers(self) -> list[APIRouter]:
        """
        The PassKit web service and public enrollment, the operator's actions and programs, the merchant's space.

        Returns:
            The four routers, mounted under the API prefix.
        """
        return [wallet.router, wallet_merchant.router, wallet_programs.router, merchant.router]

    def background_loops(self) -> list[BackgroundLoop]:
        """
        The automation worker, which fires the deferred offers onto the cards.

        Returns:
            Its loop.
        """
        return [wallet_automation_worker.run_forever]

    def migrations(self) -> list[tuple[str, str]]:
        """
        The module's tracked migrations, run after the core's.

        Returns:
            (name, dotted module path) pairs, in order.
        """
        return [(name, f"{_MIGRATIONS_PACKAGE}.{name}") for name in self.MIGRATION_NAMES]

    def campaign_offer(self) -> CampaignOffer | None:
        """
        The loyalty card the campaigns sell.

        Returns:
            The card offer.
        """
        return self._campaign_offer

    def email_template_library(self) -> list[dict[str, object]]:
        """
        The card's cold emails, appended to the shared library by the core's seeder.

        Returns:
            A copy of the five « Carte fidélité - … » templates.
        """
        return [dict(template) for template in LOYALTY_CARD_EMAIL_TEMPLATES]

    async def handle_stripe_event(self, db: Session, event: dict[str, Any]) -> str | None:
        """
        Handle a Stripe event when it belongs to a merchant's wallet subscription, and only then.

        Args:
            db: Active database session.
            event: The verified Stripe event.

        Returns:
            What was done, or None when the event carries no wallet subscription metadata.
        """
        return wallet_subscription_service.handle_stripe_event(db, event)
