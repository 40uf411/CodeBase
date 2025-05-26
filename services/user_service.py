from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import Depends

from core.database import get_async_db # Assuming this will be the new async session getter
from core.exceptions import EntityNotFoundError, DuplicateEntityError
from models.user import User
from models.role import Role # Added
from schemas.user import UserUpdate
from repositories.user_repository import UserRepository # Assuming this will be adapted for async
from repositories.role_repository import RoleRepository # Added
from core.exceptions import InvalidOperationError # Added

class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.user_repository = UserRepository(db_session)
        self.role_repository = RoleRepository(db_session) # Added

    async def update_user_profile(self, user_id: UUID, user_in: UserUpdate) -> User:
        """
        Updates a user's profile information.
        Does not handle password changes.
        """
        user = await self.user_repository.get(user_id)
        if not user:
            raise EntityNotFoundError(entity_name="User", entity_id=str(user_id))

        update_data = user_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db_session.add(user)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(user)
        except IntegrityError:
            await self.db_session.rollback()
            # Assuming the IntegrityError is due to a duplicate email or similar unique constraint
            raise DuplicateEntityError(entity_name="User", conflicting_field="email or other unique field")
        
        return user

    async def assign_role_to_user(self, user_id: UUID, role_id: UUID) -> User:
        user = await self.user_repository.get(user_id)
        if not user:
            raise EntityNotFoundError(entity_name="User", entity_id=str(user_id))

        role = await self.role_repository.get(role_id)
        if not role:
            raise EntityNotFoundError(entity_name="Role", entity_id=str(role_id))

        if role not in user.roles:
            user.roles.append(role)
            self.db_session.add(user)
            try:
                await self.db_session.commit()
                await self.db_session.refresh(user)
            except IntegrityError: # Should not happen if checks are done, but good practice
                await self.db_session.rollback()
                raise # Re-raise the original error or a custom one
        return user

    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> User:
        user = await self.user_repository.get(user_id)
        if not user:
            raise EntityNotFoundError(entity_name="User", entity_id=str(user_id))

        role = await self.role_repository.get(role_id)
        if not role:
            raise EntityNotFoundError(entity_name="Role", entity_id=str(role_id))

        if role not in user.roles:
            raise InvalidOperationError("Role not assigned to this user")

        user.roles.remove(role)
        self.db_session.add(user)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(user)
        except IntegrityError: # Should not happen
            await self.db_session.rollback()
            raise
        return user

def get_user_service(db_session: AsyncSession = Depends(get_async_db)) -> UserService:
    return UserService(db_session)
