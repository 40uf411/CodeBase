from typing import List, Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user
from models.user import User
from models.role import Role
from models.privilege import Privilege
from models.user_role import user_roles
from models.role_privilege import role_privileges


class RBACPolicy:
    """
    Role-Based Access Control (RBAC) policy enforcement.
    """
    
    @staticmethod
    async def check_permission(
        required_privilege: str,
        db: Session = Depends(get_db),
        current_user: Dict = Depends(get_current_user)
    ) -> bool:
        """
        Check if the current user has the required privilege.
        
        Args:
            required_privilege: The privilege name required for the operation
            db: Database session
            current_user: Current authenticated user
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Super admin check - super admins have all privileges
        if current_user.get("is_superadmin", False):
            return True
            
        # Get the user from database
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user:
            return False
        
        # If the user is inactive or deleted, deny access
        if user.is_deleted or not user.is_active:
            return False
            
        # Get all roles associated with the user
        user_roles_query = db.query(Role).join(
            user_roles, Role.id == user_roles.c.role_id
        ).filter(
            user_roles.c.user_id == user.id,
            Role.is_deleted == False,
            Role.is_active == True
        )
        user_roles_list = user_roles_query.all()
        
        # If no roles found, deny access
        if not user_roles_list:
            return False
            
        # Check if any role has the required privilege
        for role in user_roles_list:
            # Check if role is a wildcard role that grants all permissions
            if role.is_admin:
                return True
                
            # Get privileges for this role
            privileges_query = db.query(Privilege).join(
                role_privileges, Privilege.id == role_privileges.c.privilege_id
            ).filter(
                role_privileges.c.role_id == role.id,
                Privilege.is_deleted == False
            )
            
            role_privileges_list = privileges_query.all()
            
            # Check if required privilege exists in role's privileges
            for privilege in role_privileges_list:
                # Check exact match
                if privilege.name == required_privilege:
                    return True
                    
                # Check wildcard permissions
                if privilege.name.endswith(":*"):
                    resource_prefix = privilege.name.split(":")[0]
                    required_resource = required_privilege.split(":")[0]
                    if resource_prefix == required_resource:
                        return True
                
                # Check wildcard resource
                if privilege.name == "*" or privilege.name == "*:*":
                    return True
        
        # If we get here, no matching privilege was found
        return False
    
    @staticmethod
    def require_permission(required_privilege: str):
        """
        Dependency for requiring a specific privilege.
        
        Args:
            required_privilege: The privilege name required for the operation
            
        Returns:
            Callable: Dependency function that checks the permission
        """
        async def check_permission_dependency(
            db: Session = Depends(get_db),
            current_user: Dict = Depends(get_current_user)
        ) -> Dict:
            has_permission = await RBACPolicy.check_permission(
                required_privilege, db, current_user
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required: {required_privilege}",
                )
            
            # Return the current user so it can be used downstream
            return current_user
        
        return check_permission_dependency


# Convenience functions for common CRUD operations
def require_create(resource: str):
    """
    Require create permission for a resource.
    
    Args:
        resource: The resource name (e.g., 'user', 'post')
        
    Returns:
        Dependency that checks for 'create:{resource}' permission
    """
    return RBACPolicy.require_permission(f"create:{resource}")


def require_read(resource: str):
    """
    Require read permission for a resource.
    
    Args:
        resource: The resource name (e.g., 'user', 'post')
        
    Returns:
        Dependency that checks for 'read:{resource}' permission
    """
    return RBACPolicy.require_permission(f"read:{resource}")


def require_update(resource: str):
    """
    Require update permission for a resource.
    
    Args:
        resource: The resource name (e.g., 'user', 'post')
        
    Returns:
        Dependency that checks for 'update:{resource}' permission
    """
    return RBACPolicy.require_permission(f"update:{resource}")


def require_delete(resource: str):
    """
    Require delete permission for a resource.
    
    Args:
        resource: The resource name (e.g., 'user', 'post')
        
    Returns:
        Dependency that checks for 'delete:{resource}' permission
    """
    return RBACPolicy.require_permission(f"delete:{resource}")