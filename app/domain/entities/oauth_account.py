from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_object.oauth_provider import OAuthProvider


@dataclass
class OAuthAccount:
    id: UUID
    user_id: UUID
    provider: OAuthProvider
    provider_user_id: str
    created_at: datetime
    updated_at: datetime
