import pytest
from attrs import asdict
from sqlalchemy import inspect
from src.contexts._receipt_tracker.shared.adapters.ORM.mappers.receipt import (
    ReceiptMapper,
)
from src.contexts._receipt_tracker.shared.adapters.ORM.mappers.seller import (
    SellerMapper,
)
from src.contexts._receipt_tracker.shared.adapters.ORM.sa_models.house import (
    HousesSaModel,
)
from src.contexts._receipt_tracker.shared.adapters.ORM.sa_models.receipt import (
    ReceiptSaModel,
)
from src.contexts._receipt_tracker.shared.adapters.ORM.sa_models.seller import (
    SellerSaModel,
)
from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts._receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts.shared_kernel.domain.value_objects.address import Address
from tests.receipt_tracker.random_refs import random_address


@pytest.fixture
def sa_model_receipt() -> ReceiptSaModel:
    return ReceiptSaModel(
        id=f"35{'0'*42}",
        houses=[HousesSaModel(id="1")],
        qrcode=None,
        date=None,
        state="SP",
        seller_id=None,
        scraped=None,
        discarded=False,
        version=1,
        items=[],
        products_added=False,
    )


@pytest.fixture
def domain_model_receipt() -> Receipt:
    return Receipt(
        cfe_key=f"35{'0'*42}",
        house_ids=["1"],
        qrcode=None,
        date=None,
        state="SP",
        seller_id=None,
        scraped=None,
        discarded=False,
        version=1,
        items=[],
        products_added=False,
    )


def test_map_domain_receipt_to_sa_model(
    domain_model_receipt: Receipt,
) -> None:
    mapper = ReceiptMapper()
    sa_model = mapper.map_domain_to_sa(domain_model_receipt)
    assert sa_model.id == domain_model_receipt.id
    assert [i.id for i in sa_model.house_ids] == domain_model_receipt.house_ids
    assert sa_model.qrcode == domain_model_receipt.qrcode
    assert sa_model.date == domain_model_receipt.date
    assert sa_model.state == domain_model_receipt.state
    assert sa_model.seller_id == domain_model_receipt.seller_id
    assert sa_model.scraped == domain_model_receipt.scraped
    assert sa_model.discarded == domain_model_receipt.discarded
    assert sa_model.version == domain_model_receipt.version
    assert sa_model.items == domain_model_receipt.items
    assert sa_model.products_added == domain_model_receipt.products_added


def test_map_sa_receipt_to_domain_model(sa_model_receipt: ReceiptSaModel) -> None:
    mapper = ReceiptMapper()
    domain_model = mapper.map_sa_to_domain(sa_model_receipt)
    assert domain_model.id == sa_model_receipt.id
    assert domain_model.house_ids == [i.id for i in sa_model_receipt.house_ids]
    assert domain_model.qrcode == sa_model_receipt.qrcode
    assert domain_model.date == sa_model_receipt.date
    assert domain_model.state == sa_model_receipt.state
    assert domain_model.seller_id == sa_model_receipt.seller_id
    assert domain_model.scraped == sa_model_receipt.scraped
    assert domain_model.discarded == sa_model_receipt.discarded
    assert domain_model.version == sa_model_receipt.version
    assert domain_model.items == sa_model_receipt.items
    assert domain_model.products_added == sa_model_receipt.products_added


@pytest.fixture
def sa_model_seller() -> SellerSaModel:
    address = random_address()
    address_dict = asdict(address)
    address_dict["state"] = "SP"
    return SellerSaModel(
        name="test_name",
        id="0" * 14,
        state_registration="test_state_registration",
        **address_dict,
    )


@pytest.fixture
def domain_model_seller(sa_model_seller: SellerSaModel) -> Seller:
    address = Address(
        street=sa_model_seller.street,
        number=sa_model_seller.number,
        zip_code=sa_model_seller.zip_code,
        district=sa_model_seller.district,
        city=sa_model_seller.city,
        state=sa_model_seller.state,
        complement=sa_model_seller.complement,
        note=sa_model_seller.note,
    )
    return Seller(
        name=sa_model_seller.name,
        cnpj=sa_model_seller.id,
        state_registration=sa_model_seller.state_registration,
        address=address,
    )


def test_map_domain_receipt_to_sa_model(
    domain_model_seller: Seller,
) -> None:
    mapper = SellerMapper()
    sa_model = mapper.map_domain_to_sa(domain_model_seller)
    assert sa_model.name == domain_model_seller.name
    assert sa_model.id == domain_model_seller.cnpj
    assert sa_model.state_registration == domain_model_seller.state_registration
    assert sa_model.street == domain_model_seller.address.street
    assert sa_model.number == domain_model_seller.address.number
    assert sa_model.zip_code == domain_model_seller.address.zip_code
    assert sa_model.district == domain_model_seller.address.district
    assert sa_model.city == domain_model_seller.address.city
    assert sa_model.state == domain_model_seller.address.state
    assert sa_model.complement == domain_model_seller.address.complement
    assert sa_model.note == domain_model_seller.address.note


def test_map_sa_receipt_to_domain_model(sa_model_seller: SellerSaModel) -> None:
    mapper = SellerMapper()
    domain_model = mapper.map_sa_to_domain(sa_model_seller)
    assert domain_model.cnpj == sa_model_seller.id
    assert domain_model.name == sa_model_seller.name
    assert domain_model.state_registration == sa_model_seller.state_registration
    assert domain_model.address.street == sa_model_seller.street
    assert domain_model.address.number == sa_model_seller.number
    assert domain_model.address.zip_code == sa_model_seller.zip_code
    assert domain_model.address.district == sa_model_seller.district
    assert domain_model.address.city == sa_model_seller.city
    assert domain_model.address.state == sa_model_seller.state
    assert domain_model.address.complement == sa_model_seller.complement
    assert domain_model.address.note == sa_model_seller.note


async def test_if_sa_model_relationship_name_match_domain_model_attribute_name():
    inspector = inspect(ReceiptSaModel)
    for attribute in inspector.relationships.keys():
        assert (
            attribute in dir(Receipt)
            or f"{attribute}_id" in dir(Receipt)
            or f"{attribute}_ids" in dir(Receipt)
        )
