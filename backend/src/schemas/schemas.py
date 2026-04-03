from pydantic import BaseModel

class User(BaseModel):
    id: int
    clerk_id: str
    email: str
    name: str
    avatar_url: str
    created_at: str

    class Config:
        orm_mode = True
