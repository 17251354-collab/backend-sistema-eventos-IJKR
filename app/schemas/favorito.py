from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FavoritoResponse(BaseModel):
    id: int
    usuario_id: int
    evento_id: int
    data_favorito: Optional[datetime] = None

    class Config:
        from_attributes = True
