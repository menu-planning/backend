class AlreadyMemberOfHouseError(Exception):
    """
    Raised when an attempt is made to accept an invitation
    to a house the user is already a member of.
    """


class HouseNotFoundError(Exception):
    """
    Raised when an attempt is made to accept an invitation
    to a house that does not exist.
    """


class NotMemberOfHouseError(Exception):
    """
    Raised when an attempt is made to leave
    a house the user is not a member of.
    """


class PatientAlreadyLinkedError(Exception):
    """
    Raised when an attempt is made to link a user
    to a patient already linked.
    """


class PatientNotFoundError(Exception):
    """
    Raised when an attempt is made to link a user
    to a patient that does not exist.
    """
