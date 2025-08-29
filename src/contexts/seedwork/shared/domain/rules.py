from abc import abstractmethod


class BusinessRule:
    """This is a base class for implementing domain rules"""

    # This is an error message that broken rule reports back
    __message: str = "Business rule is broken"

    def get_message(self) -> str:
        return self.__message

    @abstractmethod
    def is_broken(self) -> bool:
        pass

    def __str__(self):
        return f"{self.__class__.__name__} {super().__str__()}"
