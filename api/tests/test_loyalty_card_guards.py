"""A template linking the loyalty-card demo (``{lien_carte}``) never leaves, whatever the sending path.

No prospect has a card demo, so each path the core guards holds a card template back, with the reason the dashboard
shows as is: « Module « Cartes Apple Wallet » désactivé » while the module is switched off (its production default),
« Pas de démo de carte de fidélité pour ce prospect » once it is on. The paths: the campaign launch and the re-enqueue
of a ready prospect, the email and SMS dispatch, the follow-up scheduling, the immediate follow-up, the SMS composer
preview, the prospect SMS send and the SMS relance. A held-back template reserves nobody for the cross-module lock.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.v1.routes.sms import preview_template
from models.campaign import Campaign, CampaignStatus
from models.demo_site import DemoSite
from models.email_log import EmailLog
from models.email_queue import EmailQueue
from models.email_template import EmailTemplate
from models.prospect_db import ProspectDB
from models.sms_config import SmsConfig
from models.user import User
from services.campaign_queue_service import CampaignQueueService
from services.email_sending_service import EmailSendingService
from services.email_variables import EmailVariables
from services.notification_service import notification_service
from services.product_module_service import product_module_service
from services.sms.sms_provider import SmsSendResult
from services.sms_relance_service import SmsRelanceCandidate, sms_relance_service
from services.sms_service import sms_service
from services.sms_variables import SmsVariables

from devleadhunter_apple_wallet.campaigns.email_templates import LOYALTY_CARD_EMAIL_TEMPLATES
from devleadhunter_apple_wallet.campaigns.loyalty_card_offer import LOYALTY_CARD_DEMO_MISSING_REASON, LoyaltyCardOffer
from devleadhunter_apple_wallet.module import AppleWalletModule

_CARD_FIRST_EMAIL = "Carte fidélité - premier contact franc"
_CARD_FOLLOW_UP_EMAIL = "Carte fidélité - relance franche"
_WEBSITE_FIRST_EMAIL_SUBJECT = "le site de {entreprise}"
_WEBSITE_FIRST_EMAIL_BODY = "<p>{salutation},</p><p>J'ai construit le site de {entreprise} : {lien_demo}</p>"
_MODULE_OFF_REASON = "Module « Cartes Apple Wallet » désactivé"


class _AsyncCallRecorder:
    """Collects the keyword arguments of a mocked async function and returns a fixed result."""

    def __init__(self, result: Any = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.result = result

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.result


class _AcceptingSmsProvider:
    """A configured SMS provider that accepts everything and keeps every text."""

    is_configured = True

    def __init__(self) -> None:
        self.texts: list[str] = []

    async def send(self, *, to_e164: str, sender: str, text: str, **options: Any) -> SmsSendResult:
        self.texts.append(text)
        return SmsSendResult(success=True, provider_message_id=f"m{len(self.texts)}", price_cents=6)


@pytest.fixture(params=[False, True], ids=["module-off", "module-on"])
def card_refusal(request: pytest.FixtureRequest, db: Session) -> str:
    """The module switched off then on, and the reason a card template is held back with in each state."""
    if not request.param:
        return _MODULE_OFF_REASON
    product_module_service.set_enabled(db, AppleWalletModule.key, True, user_id=1)
    return LOYALTY_CARD_DEMO_MISSING_REASON


@pytest.fixture
def sender(db: Session) -> User:
    """The user sending the campaigns, his public phone set for the SMS."""
    user = User(name="Marc Dupont", email="marc@example.com", hashed_password="x", contact_phone="06 12 34 56 78")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def prospect(db: Session, sender: User) -> ProspectDB:
    """A French prospect reachable by email and on a mobile."""
    row = ProspectDB(
        user_id=sender.id,
        name="Boulangerie Martin",
        category="Boulangerie",
        source="google_maps",
        email="contact@boulangerie-martin.example",
        phone="06 11 22 33 44",
        country="FR",
    )
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def sent_emails() -> Iterator[_AsyncCallRecorder]:
    """The emails handed to the sender's identity."""
    recorder = _AsyncCallRecorder(result={"success": True, "email_log_id": None})
    with patch.object(EmailSendingService, "send_via_user_identity", recorder):
        yield recorder


@pytest.fixture
def sms_provider(db: Session, sender: User) -> Iterator[_AcceptingSmsProvider]:
    """An accepting provider behind the SMS service, an open legal window and the sender's SMS name."""
    provider = _AcceptingSmsProvider()
    db.add(SmsConfig(user_id=sender.id, sender="Dibodev"))
    db.commit()
    with ExitStack() as patches:
        patches.enter_context(patch.object(sms_service, "_provider", provider))
        patches.enter_context(patch.object(sms_service, "legal_window_refusal", lambda country=None: None))
        patches.enter_context(patch.object(notification_service, "notify_sms_event", _AsyncCallRecorder()))
        yield provider


def _email_template(db: Session, sender: User, name: str) -> EmailTemplate:
    """The module's library template *name*, saved on the sender's account."""
    library = next(template for template in LOYALTY_CARD_EMAIL_TEMPLATES if template["name"] == name)
    template = EmailTemplate(
        user_id=sender.id,
        name=name,
        subject=str(library["subject"]),
        body_html=str(library["body_html"]),
        category=str(library["category"]),
        is_library=True,
    )
    db.add(template)
    db.commit()
    return template


def _website_email_template(db: Session, sender: User) -> EmailTemplate:
    """A first email selling the demo site, which the card follow-up comes after."""
    template = EmailTemplate(
        user_id=sender.id,
        name="Franc - premier contact",
        subject=_WEBSITE_FIRST_EMAIL_SUBJECT,
        body_html=_WEBSITE_FIRST_EMAIL_BODY,
        category="first_email",
        is_library=True,
    )
    db.add(template)
    db.commit()
    return template


def _campaign(db: Session, sender: User, prospect: ProspectDB, **columns: Any) -> Campaign:
    """An active campaign of *sender* holding *prospect*."""
    campaign = Campaign(user_id=sender.id, name="Cartes de fidélité", status=CampaignStatus.ACTIVE, **columns)
    campaign.prospects.append(prospect)
    db.add(campaign)
    db.commit()
    return campaign


def _claimed_initial_send(db: Session, campaign: Campaign, prospect: ProspectDB, template_id: int | None) -> EmailQueue:
    """A J1 of *campaign*, just claimed by the worker."""
    item = EmailQueue(
        user_id=campaign.user_id,
        campaign_id=campaign.id,
        prospect_id=prospect.id,
        template_id=template_id,
        queue_type="initial",
        follow_up_index=0,
        scheduled_at=datetime.now(UTC).replace(tzinfo=None),
        status="sending",
    )
    db.add(item)
    db.commit()
    return item


class TestVariables:
    def test_the_card_link_renders_empty_and_the_price_only_while_the_module_is_on(
        self, db: Session, sender: User, prospect: ProspectDB
    ) -> None:
        email_variables_off = EmailVariables.build_for_prospect(db, prospect, user_id=sender.id)
        product_module_service.set_enabled(db, AppleWalletModule.key, True, user_id=1)
        email_variables_on = EmailVariables.build_for_prospect(db, prospect, user_id=sender.id)
        sms_variables_on = SmsVariables.build_for_prospect(db, user_id=sender.id, prospect=prospect)

        assert email_variables_off[LoyaltyCardOffer.CARD_LINK] == email_variables_off[LoyaltyCardOffer.CARD_PRICE] == ""
        assert email_variables_on[LoyaltyCardOffer.CARD_LINK] == sms_variables_on[LoyaltyCardOffer.CARD_LINK] == ""
        assert (
            email_variables_on[LoyaltyCardOffer.CARD_PRICE] == sms_variables_on[LoyaltyCardOffer.CARD_PRICE] == "19 €"
        )

    def test_a_card_template_asks_no_demo_site_for_its_withdrawal_day(self) -> None:
        """``{date_expiration}`` next to ``{lien_carte}`` is the card's day: the card guard answers, not the site's."""
        template = SimpleNamespace(subject="la carte", body_html="Prête : {lien_carte}, jusqu'au {date_expiration}.")

        assert CampaignQueueService._template_uses_demo_link(template) is False


class TestEmailCampaign:
    def test_the_launch_leaves_the_prospect_out_and_reserves_nobody(
        self, db: Session, sender: User, prospect: ProspectDB, card_refusal: str
    ) -> None:
        template = _email_template(db, sender, _CARD_FIRST_EMAIL)
        campaign = _campaign(db, sender, prospect, channel="email", template_id=template.id)

        result = CampaignQueueService(db).enqueue_campaign(campaign, template_id=template.id)

        assert result.enqueued == 0
        assert result.skipped_without_offer == {"apple-wallet": [{"id": prospect.id, "name": "Boulangerie Martin"}]}
        assert result.skipped_no_demo == []
        assert db.query(EmailQueue).count() == 0
        assert prospect.contacted_by_module is None

    def test_a_ready_prospect_never_joins_the_queue(
        self, db: Session, sender: User, prospect: ProspectDB, card_refusal: str
    ) -> None:
        template = _email_template(db, sender, _CARD_FIRST_EMAIL)
        campaign = _campaign(db, sender, prospect, channel="email", template_id=template.id)

        assert CampaignQueueService(db)._enqueue_single_ready_prospect(campaign, prospect.id) is False
        assert db.query(EmailQueue).count() == 0
        assert prospect.contacted_by_module is None

    def test_a_queued_card_email_is_held_back_at_dispatch(
        self, db: Session, sender: User, prospect: ProspectDB, sent_emails: _AsyncCallRecorder, card_refusal: str
    ) -> None:
        template = _email_template(db, sender, _CARD_FIRST_EMAIL)
        campaign = _campaign(db, sender, prospect, channel="email", template_id=template.id)
        item = _claimed_initial_send(db, campaign, prospect, template.id)

        asyncio.run(CampaignQueueService(db)._dispatch(item))

        assert (item.status, item.skip_reason) == ("skipped", card_refusal)
        assert sent_emails.calls == []
        assert prospect.contacted_by_module is None

    def test_a_card_follow_up_is_held_back_when_the_sequence_is_scheduled(
        self, db: Session, sender: User, prospect: ProspectDB, card_refusal: str
    ) -> None:
        """A switched-off module's card has no demo either: the follow-up stops on the card's own reason."""
        first_email = _website_email_template(db, sender)
        follow_up = _email_template(db, sender, _CARD_FOLLOW_UP_EMAIL)
        campaign = _campaign(db, sender, prospect, channel="email", template_id=first_email.id)
        sent_first_email = _claimed_initial_send(db, campaign, prospect, first_email.id)
        follow_up_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=3)

        is_queued = CampaignQueueService(db)._offer_link_outlives(
            sent_first_email, follow_up_at, template_id=follow_up.id
        )

        assert is_queued is False
        held_back = db.query(EmailQueue).filter(EmailQueue.queue_type == "followup").one()
        assert (held_back.status, held_back.skip_reason) == ("skipped", LOYALTY_CARD_DEMO_MISSING_REASON)

    def test_an_immediate_follow_up_answers_the_reason(
        self, db: Session, sender: User, prospect: ProspectDB, sent_emails: _AsyncCallRecorder, card_refusal: str
    ) -> None:
        template = _email_template(db, sender, _CARD_FOLLOW_UP_EMAIL)
        campaign = _campaign(db, sender, prospect, channel="email", template_id=template.id)

        result = asyncio.run(CampaignQueueService(db).send_followup_now(campaign, prospect.id, template.id))

        assert result == {"success": False, "error": card_refusal}
        assert sent_emails.calls == []


class TestSmsCampaign:
    def test_the_launch_leaves_the_prospect_out_and_reserves_nobody(
        self,
        db: Session,
        sender: User,
        prospect: ProspectDB,
        sms_provider: _AcceptingSmsProvider,
        card_refusal: str,
    ) -> None:
        campaign = _campaign(db, sender, prospect, channel="sms", sms_template_key="carte-direct")

        result = CampaignQueueService(db).enqueue_campaign(campaign)

        assert result.enqueued == 0
        assert result.skipped_without_offer == {"apple-wallet": [{"id": prospect.id, "name": "Boulangerie Martin"}]}
        assert result.skipped_no_demo == []
        assert db.query(EmailQueue).count() == 0
        assert prospect.contacted_by_module is None

    def test_a_queued_card_sms_is_held_back_at_dispatch(
        self,
        db: Session,
        sender: User,
        prospect: ProspectDB,
        sms_provider: _AcceptingSmsProvider,
        card_refusal: str,
    ) -> None:
        campaign = _campaign(db, sender, prospect, channel="sms", sms_template_key="carte-direct")
        item = _claimed_initial_send(db, campaign, prospect, None)

        asyncio.run(CampaignQueueService(db)._dispatch(item))

        assert (item.status, item.skip_reason) == ("skipped", card_refusal)
        assert sms_provider.texts == []
        assert prospect.contacted_by_module is None


class TestSmsSends:
    def test_the_composer_preview_answers_the_reason(
        self, db: Session, sender: User, prospect: ProspectDB, card_refusal: str
    ) -> None:
        with pytest.raises(HTTPException) as refusal:
            asyncio.run(preview_template("carte-direct", prospect.id, current_user=sender, db=db))

        assert (refusal.value.status_code, refusal.value.detail) == (400, card_refusal)

    def test_a_prospect_send_answers_the_reason(
        self,
        db: Session,
        sender: User,
        prospect: ProspectDB,
        sms_provider: _AcceptingSmsProvider,
        card_refusal: str,
    ) -> None:
        config = db.query(SmsConfig).filter(SmsConfig.user_id == sender.id).one()

        outcome = asyncio.run(
            sms_service.send_to_prospect(
                db,
                user_id=sender.id,
                prospect=prospect,
                config=config,
                demo_url="",
                cold=True,
                template_key="carte-direct",
            )
        )

        assert (outcome.sent, outcome.reason) == (False, card_refusal)
        assert sms_provider.texts == []

    @pytest.mark.parametrize(("template_key", "should_send"), [("rappel-court", True), ("carte-relance", False)])
    def test_the_relance_never_sends_a_card_template(
        self,
        db: Session,
        sender: User,
        prospect: ProspectDB,
        sms_provider: _AcceptingSmsProvider,
        card_refusal: str,
        template_key: str,
        should_send: bool,
    ) -> None:
        """The same emailed prospect gets the website relance, never the card one."""
        emailed_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=40)
        db.add(
            EmailLog(
                user_id=sender.id,
                prospect_id=prospect.id,
                recipient_email=str(prospect.email),
                subject="le site de Boulangerie Martin",
                body_html="<p>Bonjour</p>",
                provider="resend",
                status="sent",
                sent_at=emailed_at,
            )
        )
        site = DemoSite(
            user_id=sender.id,
            prospect_id=prospect.id,
            slug="boulangerie-martin",
            business_name="Boulangerie Martin",
            status="active",
            expires_at=datetime.now(UTC) + timedelta(days=10),
        )
        db.add(site)
        db.commit()
        candidate = SmsRelanceCandidate(
            prospect=prospect,
            demo_site=site,
            demo_url="https://demo.dibodev.fr/s/boulangerie-martin",
            emailed_at=emailed_at,
        )

        was_sent = asyncio.run(sms_relance_service.send_relance(db, sender.id, candidate, template_key=template_key))

        assert was_sent is should_send
        assert len(sms_provider.texts) == (1 if should_send else 0)
