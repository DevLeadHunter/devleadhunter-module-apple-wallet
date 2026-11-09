"""The Apple Wallet module as the core loads it: identity, switch, routes, worker, migrations and Stripe events."""

from __future__ import annotations

import asyncio
import importlib
import tomllib
from collections.abc import Iterator
from importlib.metadata import EntryPoint
from pathlib import Path

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.v1.product_module_mounting import include_product_module_routers
from core.database import get_db
from core.product_modules.contract import ENTRY_POINT_GROUP
from core.product_modules.registry import ProductModuleRegistry
from migrations.run_migrations import MIGRATION_MODULES, _all_migrations
from models.user import User
from services.auth_service import AuthService
from services.product_module_service import product_module_service

from devleadhunter_apple_wallet.enums.wallet_subscription_status import WalletSubscriptionStatus
from devleadhunter_apple_wallet.models.loyalty_program import LoyaltyProgram
from devleadhunter_apple_wallet.models.wallet_subscription import WalletSubscription
from devleadhunter_apple_wallet.module import AppleWalletModule
from devleadhunter_apple_wallet.services.wallet_automation_service import (
    WalletAutomationWorker,
    wallet_automation_worker,
)

_API_ROOT = Path(__file__).resolve().parents[1]
_MIGRATIONS_DIRECTORY = _API_ROOT / "devleadhunter_apple_wallet" / "migrations"
_NON_MIGRATION_FILES = frozenset({"__init__", "schema_changes"})


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """The installed modules' routers mounted the way the core mounts them, on the test's database."""
    app = FastAPI()
    v1_router = APIRouter()
    include_product_module_routers(v1_router)
    app.include_router(v1_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client


class TestIdentity:
    def test_the_module_ships_switched_off(self, db: Session, apple_wallet_module_installed: AppleWalletModule) -> None:
        assert (AppleWalletModule.key, AppleWalletModule.label) == ("apple-wallet", "Cartes Apple Wallet")
        assert AppleWalletModule.enabled_by_default is False
        assert product_module_service.is_enabled(db, "apple-wallet") is False
        assert product_module_service.enabled_modules(db) == []

    def test_the_super_admin_switches_it_on(
        self, db: Session, apple_wallet_module_switched_on: AppleWalletModule
    ) -> None:
        assert [module.key for module in product_module_service.enabled_modules(db)] == ["apple-wallet"]

    def test_the_declared_entry_point_loads_the_module(self) -> None:
        pyproject = tomllib.loads((_API_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        declared = pyproject["project"]["entry-points"][ENTRY_POINT_GROUP]
        assert declared == {"apple-wallet": "devleadhunter_apple_wallet.module:AppleWalletModule"}

        registry = ProductModuleRegistry()
        entry_point = EntryPoint(name="apple-wallet", value=declared["apple-wallet"], group=ENTRY_POINT_GROUP)
        module = registry._load_entry_point(entry_point)

        assert isinstance(module, AppleWalletModule)
        assert registry.load_failures() == {}


class TestRoutes:
    def test_every_route_answers_404_while_the_module_is_off(self, client: TestClient) -> None:
        for method, path in (
            ("GET", "/api/v1/wallet/enroll/any-token"),
            ("POST", "/api/v1/wallet/add/any-token"),
            ("GET", "/api/v1/wallet/v1/devices/device/registrations/pass.x"),
            ("GET", "/api/v1/wallet/programs"),
            ("POST", "/api/v1/wallet/merchant/scan"),
            ("POST", "/api/v1/merchant/login"),
            ("GET", "/api/v1/merchant/me"),
        ):
            response = client.request(method, path, json={})
            assert (response.status_code, response.json()) == (404, {"detail": "Module désactivé"}), path

    def test_the_routes_open_once_the_module_is_on(
        self, client: TestClient, apple_wallet_module_switched_on: AppleWalletModule
    ) -> None:
        unknown_program = client.get("/api/v1/wallet/enroll/any-token")
        assert (unknown_program.status_code, unknown_program.json()) == (404, {"detail": "Programme introuvable"})
        assert client.get("/api/v1/wallet/programs").status_code == 401
        assert client.get("/api/v1/merchant/me").status_code == 401
        refused_login = client.post("/api/v1/merchant/login", json={"email": "x@merchant.dibodev.fr", "password": "x"})
        assert (refused_login.status_code, refused_login.json()) == (401, {"detail": "Identifiants invalides"})
        assert client.get("/api/v1/wallet/v1/devices/device/registrations/pass.x").status_code == 204

    def test_the_operator_routes_no_longer_ask_a_per_user_activation(
        self, client: TestClient, db: Session, apple_wallet_module_switched_on: AppleWalletModule
    ) -> None:
        """The core's switch replaced the old per-user gate: a logged-in operator reaches his programs at once."""
        operator = User(name="Marc Dupont", email="marc@example.com", hashed_password="x")
        db.add(operator)
        db.commit()
        token = AuthService.create_access_token({"sub": operator.email})

        response = client.get("/api/v1/wallet/programs", headers={"Authorization": f"Bearer {token}"})

        assert (response.status_code, response.json()) == (200, [])


class TestWorker:
    def test_the_core_runs_the_automation_worker(self, apple_wallet_module_installed: AppleWalletModule) -> None:
        assert apple_wallet_module_installed.background_loops() == [wallet_automation_worker.run_forever]

    def test_a_pass_reports_the_jobs_it_fired_and_survives_a_failure(self) -> None:
        class _Service:
            def __init__(self, outcome: int | Exception) -> None:
                self._outcome = outcome

            def run_due_jobs(self) -> int:
                if isinstance(self._outcome, Exception):
                    raise self._outcome
                return self._outcome

        assert asyncio.run(WalletAutomationWorker(_Service(2)).run_once()) == 2  # type: ignore[arg-type]
        assert asyncio.run(WalletAutomationWorker(_Service(RuntimeError("db down"))).run_once()) == 0  # type: ignore[arg-type]


class TestMigrations:
    def test_the_migrations_run_after_the_core_ones(self, apple_wallet_module_installed: AppleWalletModule) -> None:
        listed = _all_migrations()

        assert listed[: len(MIGRATION_MODULES)] == MIGRATION_MODULES
        assert listed[len(MIGRATION_MODULES) :] == apple_wallet_module_installed.migrations()
        assert [name for name, _ in apple_wallet_module_installed.migrations()][
            -1
        ] == "add_loyalty_card_email_templates"

    def test_every_migration_file_is_registered_and_runnable(
        self, apple_wallet_module_installed: AppleWalletModule
    ) -> None:
        """An unregistered migration would never run: the column would stay absent in production."""
        on_disk = {path.stem for path in _MIGRATIONS_DIRECTORY.glob("*.py")} - _NON_MIGRATION_FILES
        registered = dict(apple_wallet_module_installed.migrations())

        assert set(registered) == on_disk
        for name, module_path in registered.items():
            assert module_path == f"devleadhunter_apple_wallet.migrations.{name}"
            assert callable(importlib.import_module(module_path).run_migration), name

    def test_no_migration_name_collides_with_a_core_one(self, apple_wallet_module_installed: AppleWalletModule) -> None:
        core_names = {name for name, _ in MIGRATION_MODULES}
        assert core_names.isdisjoint(name for name, _ in apple_wallet_module_installed.migrations())


class TestStripeEvents:
    def test_only_the_wallet_subscription_events_are_claimed_even_while_off(
        self, db: Session, apple_wallet_module_installed: AppleWalletModule
    ) -> None:
        """Billing follows Stripe whatever the switch: the module is off here, and still syncs its subscription."""
        program = LoyaltyProgram(user_id=1, organization_name="Café Mirabeau", stamps_required=10)
        db.add(program)
        db.flush()
        db.add(
            WalletSubscription(
                user_id=1,
                program_id=program.id,
                status=WalletSubscriptionStatus.TRIALING.value,
                stripe_subscription_id="sub_wallet",
            )
        )
        db.commit()
        wallet_update = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_wallet",
                    "status": "past_due",
                    "metadata": {"type": "wallet_subscription", "program_id": str(program.id)},
                }
            },
        }
        site_order = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_1", "mode": "payment", "metadata": {"order_id": "7"}}},
        }
        receptionist_update = {
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_receptionist", "status": "active", "metadata": {"assistant_id": "3"}}},
        }

        assert asyncio.run(apple_wallet_module_installed.handle_stripe_event(db, site_order)) is None
        assert asyncio.run(apple_wallet_module_installed.handle_stripe_event(db, receptionist_update)) is None
        assert asyncio.run(apple_wallet_module_installed.handle_stripe_event(db, wallet_update)) == (
            "Wallet subscription synced"
        )
        assert db.query(WalletSubscription).one().status == WalletSubscriptionStatus.PAST_DUE.value
