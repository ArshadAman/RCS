from rest_framework import permissions


class IsBusinessOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a business to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the business
        # or the owner of the company that owns the business.
        return obj.owner == request.user or obj.company.owner == request.user


class IsReviewOwnerOrBusinessOwner(permissions.BasePermission):
    """
    Custom permission to only allow review owners or business owners to edit reviews.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to:
        # - The review owner (customer)
        # - The business owner
        # - The company owner
        # - Staff users
        return (
            obj.reviewer == request.user or
            obj.business.owner == request.user or
            obj.business.company.owner == request.user or
            request.user.is_staff
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user if hasattr(obj, 'owner') else False


class IsCompanyMemberOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow company members to edit company-related objects.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to company members.
        if hasattr(obj, 'company'):
            return obj.company.owner == request.user
        elif hasattr(obj, 'business'):
            return obj.business.company.owner == request.user
        
        return False
