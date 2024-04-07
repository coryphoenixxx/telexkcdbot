from pydantic import BaseModel, SecretStr


class UserRequestSchema(BaseModel):
    username: str
    raw_password: SecretStr

    @property
    def secret(self):
        return self.raw_password.get_secret_value()
