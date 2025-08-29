from enum import Enum, unique


@unique
class FrontendFilterTypes(Enum):
    SINGLE_SELECTION = "single_selection"
    MULTI_SELECTION = "multi_selection"
    SORT = "sort"
    SWITCH = "switch"
    EXPANDABLE_SWITCH = "expandable_switch"
    DATE_SELECTION = "date_selection"
