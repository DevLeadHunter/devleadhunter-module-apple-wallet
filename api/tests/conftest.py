"""The module's tests run on the core's fixtures, from the core's ``api/``.

``python -m pytest ../../devleadhunter-module-apple-wallet/api/tests`` from the core's ``api/``: ``tests`` then names the
core's test package (this folder has no ``__init__.py``, so it never shadows it), whose fixtures give each test an
in-memory database with every table — the module's included, its models being loaded below — and keep the outside
world offline. The core's own autouse fixture leaves no module installed; the one here installs the Apple Wallet module
after it, switched off as in production, until a test asks for ``apple_wallet_module_switched_on``.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from core.product_modules.registry import product_module_registry
from services.product_module_service import product_module_service
from tests.conftest import *  # noqa: F403

from devleadhunter_apple_wallet.module import AppleWalletModule

_APPLE_WALLET_MODULE: AppleWalletModule = AppleWalletModule()
_APPLE_WALLET_MODULE.load()


@pytest.fixture(autouse=True)
def apple_wallet_module_installed(no_product_module_installed: None) -> Iterator[AppleWalletModule]:
    """The Apple Wallet module installed next to the core and switched off, its production default."""
    product_module_registry.use([_APPLE_WALLET_MODULE])
    yield _APPLE_WALLET_MODULE


@pytest.fixture
def apple_wallet_module_switched_on(db: Session, apple_wallet_module_installed: AppleWalletModule) -> AppleWalletModule:
    """The module switched on in the test database, the way the super admin does it."""
    product_module_service.set_enabled(db, AppleWalletModule.key, True, user_id=1)
    return apple_wallet_module_installed
