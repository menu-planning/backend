"""Performance tests for API schema serialization operations.

Tests serialization performance for shared kernel API schemas including
ApiAddress, ApiNutriFacts, ApiContactInfo, ApiProfile, and ApiTag schemas.

Performance targets:
- Simple schema serialization: P95 < 1ms
- Complex schema serialization (ApiNutriFacts): P95 < 5ms
- Bulk serialization (100 items): P95 < 50ms
- JSON serialization: P95 < 2ms
"""

import json
import time

import pytest
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_address import (
    ApiAddress,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import (
    ApiContactInfo,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import (
    ApiProfile,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit, State
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class AsyncBenchmarkTimer:
    """Context manager for measuring async operation performance with warmup and sampling."""

    def __init__(self, max_ms: float, samples: int = 30, warmup: int = 5):
        """Initialize benchmark timer.

        Args:
            max_ms: Maximum allowed milliseconds for P95 threshold.
            samples: Number of samples to collect for measurement.
            warmup: Number of warmup iterations before measurement.
        """
        self.max_ms = max_ms
        self.samples = samples
        self.warmup = warmup
        self.times: list[float] = []

    def __enter__(self):
        """Enter context and start timing."""
        self.times = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and validate performance threshold."""
        if exc_type is not None:
            return False

        if len(self.times) < self.samples:
            pytest.fail(f"Expected {self.samples} samples, got {len(self.times)}")

        # Calculate P95
        sorted_times = sorted(self.times)
        p95_index = int(0.95 * len(sorted_times))
        p95_time = sorted_times[p95_index]

        if p95_time > self.max_ms:
            pytest.fail(
                f"P95 time {p95_time:.2f}ms exceeds threshold {self.max_ms}ms. "
                f"Times: {sorted_times[:5]}...{sorted_times[-5:]}"
            )

    async def measure(self, operation):
        """Measure a single operation and record its execution time."""
        start_time = time.perf_counter()
        if callable(operation):
            operation()
        else:
            await operation()
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        self.times.append(duration_ms)


@pytest.fixture
def async_benchmark_timer():
    """Provide async benchmark timer for performance measurements."""
    return AsyncBenchmarkTimer


@pytest.fixture
def seed_data():
    """Provide seed data for performance testing."""
    return {
        "simple_address": {
            "street": "123 Main St",
            "number": "456",
            "zip_code": "12345",
            "district": "Downtown",
            "city": "Anytown",
            "state": State.SP,
            "complement": "Apt 1",
            "note": "Test address",
        },
        "complex_nutri_facts": {
            "calories": {"value": 250.0, "unit": "kcal"},
            "protein": {"value": 15.0, "unit": "g"},
            "carbohydrate": {"value": 30.0, "unit": "g"},
            "total_fat": {"value": 10.0, "unit": "g"},
            "saturated_fat": {"value": 3.0, "unit": "g"},
            "trans_fat": {"value": 0.0, "unit": "g"},
            "dietary_fiber": {"value": 5.0, "unit": "g"},
            "sodium": {"value": 200.0, "unit": "mg"},
            "vitamin_a": {"value": 100.0, "unit": "mcg"},
            "vitamin_c": {"value": 50.0, "unit": "mg"},
            "calcium": {"value": 150.0, "unit": "mg"},
            "iron": {"value": 2.0, "unit": "mg"},
        },
        "contact_info": {
            "main_phone": "+1234567890",
            "main_email": "test@example.com",
            "all_phones": frozenset(["+1234567890"]),
            "all_emails": frozenset(["test@example.com"]),
        },
        "profile": {
            "name": "John Doe",
            "sex": "masculino",
            "birthday": None,
        },
        "tag": {
            "key": "cuisine",
            "value": "italian",
            "author_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "category",
        },
    }


@pytest.fixture
def bulk_address_data(seed_data):
    """Generate bulk address data for performance testing."""
    base_address = seed_data["simple_address"]
    return [
        {**base_address, "street": f"{base_address['street']} #{i}"} for i in range(100)
    ]


@pytest.fixture
def bulk_nutri_facts_data(seed_data):
    """Generate bulk nutrition facts data for performance testing."""
    base_nutri = seed_data["complex_nutri_facts"]
    return [
        {
            **base_nutri,
            "calories": {
                "value": base_nutri["calories"]["value"] + i,
                "unit": "kcal",
            },
        }
        for i in range(100)
    ]


@pytest.mark.slow
@pytest.mark.anyio
async def test_api_address_serialization_performance(async_benchmark_timer, seed_data):
    """Test ApiAddress serialization meets performance requirements."""
    address_data = seed_data["simple_address"]

    # Warmup
    for _ in range(5):
        ApiAddress(**address_data)
        ApiAddress(**address_data).model_dump()

    with async_benchmark_timer(max_ms=1.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiAddress(**address_data))
            await timer.measure(lambda: ApiAddress(**address_data).model_dump())


@pytest.mark.slow
@pytest.mark.anyio
async def test_api_nutri_facts_serialization_performance(
    async_benchmark_timer, seed_data
):
    """Test ApiNutriFacts serialization meets performance requirements."""
    nutri_data = seed_data["complex_nutri_facts"]

    # Warmup
    for _ in range(5):
        ApiNutriFacts(**nutri_data)
        ApiNutriFacts(**nutri_data).model_dump()

    with async_benchmark_timer(max_ms=5.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiNutriFacts(**nutri_data))
            await timer.measure(lambda: ApiNutriFacts(**nutri_data).model_dump())


@pytest.mark.slow
@pytest.mark.anyio
async def test_api_contact_info_serialization_performance(
    async_benchmark_timer, seed_data
):
    """Test ApiContactInfo serialization meets performance requirements."""
    contact_data = seed_data["contact_info"]

    # Warmup
    for _ in range(5):
        ApiContactInfo(**contact_data)
        ApiContactInfo(**contact_data).model_dump()

    with async_benchmark_timer(max_ms=1.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiContactInfo(**contact_data))
            await timer.measure(lambda: ApiContactInfo(**contact_data).model_dump())


@pytest.mark.slow
@pytest.mark.anyio
async def test_api_profile_serialization_performance(async_benchmark_timer, seed_data):
    """Test ApiProfile serialization meets performance requirements."""
    profile_data = seed_data["profile"]

    # Warmup
    for _ in range(5):
        ApiProfile(**profile_data)
        ApiProfile(**profile_data).model_dump()

    with async_benchmark_timer(max_ms=1.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiProfile(**profile_data))
            await timer.measure(lambda: ApiProfile(**profile_data).model_dump())


@pytest.mark.slow
@pytest.mark.anyio
async def test_api_tag_serialization_performance(async_benchmark_timer, seed_data):
    """Test ApiTag serialization meets performance requirements."""
    tag_data = seed_data["tag"]

    # Warmup
    for _ in range(5):
        ApiTag(**tag_data)
        ApiTag(**tag_data).model_dump()

    with async_benchmark_timer(max_ms=1.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiTag(**tag_data))
            await timer.measure(lambda: ApiTag(**tag_data).model_dump())


@pytest.mark.slow
@pytest.mark.anyio
async def test_json_serialization_performance(async_benchmark_timer, seed_data):
    """Test JSON serialization performance for API schemas."""
    address = ApiAddress(**seed_data["simple_address"])
    nutri_facts = ApiNutriFacts(**seed_data["complex_nutri_facts"])
    contact_info = ApiContactInfo(**seed_data["contact_info"])
    profile = ApiProfile(**seed_data["profile"])
    tag = ApiTag(**seed_data["tag"])

    schemas = [address, nutri_facts, contact_info, profile, tag]

    # Warmup
    for schema in schemas:
        for _ in range(2):
            data = schema.model_dump()
            if hasattr(schema, "all_phones") and isinstance(
                data.get("all_phones"), frozenset
            ):
                data["all_phones"] = list(data["all_phones"])
            if hasattr(schema, "all_emails") and isinstance(
                data.get("all_emails"), frozenset
            ):
                data["all_emails"] = list(data["all_emails"])
            json.dumps(data)

    with async_benchmark_timer(max_ms=2.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            for schema in schemas:
                # Convert frozensets to lists for JSON serialization
                data = schema.model_dump()
                if hasattr(schema, "all_phones") and isinstance(
                    data.get("all_phones"), frozenset
                ):
                    data["all_phones"] = list(data["all_phones"])
                if hasattr(schema, "all_emails") and isinstance(
                    data.get("all_emails"), frozenset
                ):
                    data["all_emails"] = list(data["all_emails"])
                await timer.measure(lambda d=data: json.dumps(d))


@pytest.mark.slow
@pytest.mark.anyio
async def test_bulk_address_serialization_performance(
    async_benchmark_timer, bulk_address_data
):
    """Test bulk address serialization meets performance requirements."""
    # Warmup
    for _ in range(2):
        [ApiAddress(**data) for data in bulk_address_data[:10]]

    with async_benchmark_timer(max_ms=50.0, samples=10, warmup=2) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: [ApiAddress(**data) for data in bulk_address_data]
            )


@pytest.mark.slow
@pytest.mark.anyio
async def test_bulk_nutri_facts_serialization_performance(
    async_benchmark_timer, bulk_nutri_facts_data
):
    """Test bulk nutrition facts serialization meets performance requirements."""
    # Warmup
    for _ in range(2):
        [ApiNutriFacts(**data) for data in bulk_nutri_facts_data[:10]]

    with async_benchmark_timer(max_ms=100.0, samples=10, warmup=2) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: [ApiNutriFacts(**data) for data in bulk_nutri_facts_data]
            )


@pytest.mark.slow
@pytest.mark.anyio
async def test_domain_conversion_performance(async_benchmark_timer, seed_data):
    """Test domain model conversion performance."""
    # Create domain objects
    address = Address(
        street=seed_data["simple_address"]["street"],
        number=seed_data["simple_address"]["number"],
        zip_code=seed_data["simple_address"]["zip_code"],
        district=seed_data["simple_address"]["district"],
        city=seed_data["simple_address"]["city"],
        state=State(seed_data["simple_address"]["state"]),
        complement=seed_data["simple_address"]["complement"],
        note=seed_data["simple_address"]["note"],
    )

    nutri_facts = NutriFacts(
        calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
        protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
        carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
        total_fat=NutriValue(value=10.0, unit=MeasureUnit.GRAM),
    )

    contact_info = ContactInfo(
        main_phone=seed_data["contact_info"]["main_phone"],
        main_email=seed_data["contact_info"]["main_email"],
        all_phones=seed_data["contact_info"]["all_phones"],
        all_emails=seed_data["contact_info"]["all_emails"],
    )

    profile = Profile(
        name=seed_data["profile"]["name"],
        sex=seed_data["profile"]["sex"],
        birthday=seed_data["profile"]["birthday"],
    )

    tag = Tag(
        key=seed_data["tag"]["key"],
        value=seed_data["tag"]["value"],
        author_id=seed_data["tag"]["author_id"],
        type=seed_data["tag"]["type"],
    )

    # Warmup
    for _ in range(5):
        ApiAddress.from_domain(address)
        ApiNutriFacts.from_domain(nutri_facts)
        ApiContactInfo.from_domain(contact_info)
        ApiProfile.from_domain(profile)
        ApiTag.from_domain(tag)

    with async_benchmark_timer(max_ms=3.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiAddress.from_domain(address))
            await timer.measure(lambda: ApiNutriFacts.from_domain(nutri_facts))
            await timer.measure(lambda: ApiContactInfo.from_domain(contact_info))
            await timer.measure(lambda: ApiProfile.from_domain(profile))
            await timer.measure(lambda: ApiTag.from_domain(tag))


@pytest.mark.slow
@pytest.mark.anyio
async def test_serialization_roundtrip_performance(async_benchmark_timer, seed_data):
    """Test serialization roundtrip performance (domain -> API -> domain)."""
    # Create domain objects
    address = Address(
        street=seed_data["simple_address"]["street"],
        number=seed_data["simple_address"]["number"],
        zip_code=seed_data["simple_address"]["zip_code"],
        district=seed_data["simple_address"]["district"],
        city=seed_data["simple_address"]["city"],
        state=State(seed_data["simple_address"]["state"]),
        complement=seed_data["simple_address"]["complement"],
        note=seed_data["simple_address"]["note"],
    )

    nutri_facts = NutriFacts(
        calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
        protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
        carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
        total_fat=NutriValue(value=10.0, unit=MeasureUnit.GRAM),
    )

    # Warmup
    for _ in range(5):
        api_address = ApiAddress.from_domain(address)
        api_address.to_domain()
        api_nutri = ApiNutriFacts.from_domain(nutri_facts)
        api_nutri.to_domain()

    with async_benchmark_timer(max_ms=5.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiAddress.from_domain(address).to_domain())
            await timer.measure(
                lambda: ApiNutriFacts.from_domain(nutri_facts).to_domain()
            )


@pytest.mark.slow
@pytest.mark.anyio
async def test_validation_performance(async_benchmark_timer, seed_data):
    """Test validation performance for complex schemas."""
    nutri_data = seed_data["complex_nutri_facts"]

    # Warmup
    for _ in range(5):
        ApiNutriFacts(**nutri_data)

    with async_benchmark_timer(max_ms=3.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: ApiNutriFacts(**nutri_data))


@pytest.mark.slow
@pytest.mark.anyio
async def test_arithmetic_operations_performance(async_benchmark_timer, seed_data):
    """Test arithmetic operations performance for ApiNutriFacts."""
    nutri_data = seed_data["complex_nutri_facts"]
    nutri1 = ApiNutriFacts(**nutri_data)
    nutri2 = ApiNutriFacts(**nutri_data)

    # Warmup
    for _ in range(5):
        _ = nutri1 + nutri2
        _ = nutri1 - nutri2
        _ = nutri1 * 2.0
        _ = nutri1 / 2.0

    with async_benchmark_timer(max_ms=2.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: nutri1 + nutri2)
            await timer.measure(lambda: nutri1 - nutri2)
            await timer.measure(lambda: nutri1 * 2.0)
            await timer.measure(lambda: nutri1 / 2.0)
