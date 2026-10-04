"""Acceptance test for option reference integrity before quote enrichment."""

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.options import option_chain_frame, validate_option_reference  # noqa: E402

frame = option_chain_frame(
    symbol="AAPL",
    underlying_con_id=265598,
    exchange="SMART",
    trading_class="AAPL",
    multiplier="100",
    expirations={"20261030", "20261120"},
    strikes={330.0, 335.0},
    observed_at=datetime(2026, 10, 4, tzinfo=UTC),
)
validated = validate_option_reference(frame)
assert len(validated) == 4
assert validated["expiration"].nunique() == 2
assert validated["strike"].nunique() == 2
print("PASS option reference integrity; quote surface awaits market-data entitlement")
