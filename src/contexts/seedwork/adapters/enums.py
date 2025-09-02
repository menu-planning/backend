from enum import Enum, unique


@unique
class FrontendFilterTypes(Enum):
    """Frontend filter type enumeration for UI components.

    Defines the types of filter controls that can be rendered in the frontend.
    """
    SINGLE_SELECTION = "single_selection"
    MULTI_SELECTION = "multi_selection"
    SORT = "sort"
    SWITCH = "switch"
    EXPANDABLE_SWITCH = "expandable_switch"
    DATE_SELECTION = "date_selection"
