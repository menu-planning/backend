from pydantic import BaseModel


class ApiDeleteClient(BaseModel):
    client_id: str
