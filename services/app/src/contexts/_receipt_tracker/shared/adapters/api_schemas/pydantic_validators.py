from typing import Annotated, Any

from pydantic import BeforeValidator
from src.contexts._receipt_tracker.shared.domain.enums import CfeStateCodes


def _cfe_key(v: Any):
    if len(v) != 44:
        raise ValueError(f"Cfe key must have 44 digits. Got {len(v)}")
    try:
        state_code = int(str(int(v))[:2])
    except ValueError as e:
        raise ValueError(f"Cfe key must contain only numbers. cfe_key={v}") from e
    try:
        CfeStateCodes(state_code).name
    except ValueError as e:
        raise ValueError(f"There is no state with receipt code={state_code}.") from e
    if int(v[:2]) not in [p.value for p in CfeStateCodes]:
        raise ValueError(f"Unknown state: {v}")
    return v


CfeKeyStr = Annotated[str, BeforeValidator(_cfe_key)]


def _cnpj(v: Any):
    v = str(v)
    if len(v) != 14:
        raise ValueError(f"Invalid lenght CNPJ={len(v)}")
    try:
        int(v)
    except ValueError as e:
        raise ValueError("CNPJ must contain only numbers.") from e
    return v


CNPJStr = Annotated[str | None, BeforeValidator(_cnpj)]
