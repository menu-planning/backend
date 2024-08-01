from typing import Annotated

from sqlalchemy.orm import mapped_column

strpk = Annotated[str, mapped_column(primary_key=True)]
str_required_idx = Annotated[str, mapped_column(nullable=False, index=True)]