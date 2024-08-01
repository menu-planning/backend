from src.contexts.seedwork.shared.domain.rules import BusinessRule


class NonNegativeFloat(BusinessRule):
    __message = "Value must be a non-negative float"

    def __init__(self, value: float):
        self.value = value

    def is_broken(self) -> bool:
        return self.value <= 0

    def get_message(self) -> str:
        return self.__message


class CanNotChangeProductOfItemWithUniqueBarcode(BusinessRule):
    __message = (
        "Items representing a product with an unique barcode can not change the product"
    )

    def __init__(self, product_id: str | None, is_barcode_unique: str):
        self.product_id = product_id
        self.is_barcode_unique = is_barcode_unique

    def is_broken(self) -> bool:
        return self.product_id is not None and self.is_barcode_unique

    def get_message(self) -> str:
        return self.__message


class CanNotChangeIsFoodAttributeOfItemWithUniqueBarcode(BusinessRule):
    __message = "Items representing a product with an unique barcode can not change is_food attribute"

    def __init__(self, product_id: str | None, is_barcode_unique: str):
        self.product_id = product_id
        self.is_barcode_unique = is_barcode_unique

    def is_broken(self) -> bool:
        return self.product_id is not None and self.is_barcode_unique

    def get_message(self) -> str:
        return self.__message
