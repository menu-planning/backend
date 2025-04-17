from pydantic import BaseModel


class ApiDeleteMenu(BaseModel):
    client_id: str
    menu_id: str
