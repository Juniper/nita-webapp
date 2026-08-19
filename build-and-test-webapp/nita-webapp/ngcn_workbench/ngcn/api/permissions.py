# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Role-based DRF permission classes for the NITA Webapp API.

Access control is driven by the ``role`` field on the custom user model
(``ngcn.User``): one of ``user``, ``power_user`` or ``admin``. Django's
``is_staff`` / ``is_superuser`` flags are intentionally NOT consulted here — they
gate the Django admin panel only.

Classes
-------
``IsAdminRole``
    Only ``role == "admin"``.
``IsPowerUserOrAdmin``
    ``role in ("power_user", "admin")``.
``IsOwnerOrAdmin``
    Object-level: the requesting user owns the object (``owner`` or
    ``created_by``) or is an admin.
``IsOwnerOrTeamMemberOrAdmin``
    Object-level for networks: owner, a member of the object's team, or admin.
    Team members get read-only access (writes require ownership or admin).
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from ngcn.models import User


def _role(user):
    """Return the application role for ``user`` or ``None`` if unauthenticated."""
    if not user or not user.is_authenticated:
        return None
    return getattr(user, "role", None)


class IsAdminRole(BasePermission):
    """Grant access only to users with ``role == "admin"``."""

    def has_permission(self, request, view):
        return _role(request.user) == User.ROLE_ADMIN

    def has_object_permission(self, request, view, obj):
        return _role(request.user) == User.ROLE_ADMIN


class IsPowerUserOrAdmin(BasePermission):
    """Grant access to ``power_user`` and ``admin`` roles."""

    def has_permission(self, request, view):
        return _role(request.user) in (User.ROLE_POWER_USER, User.ROLE_ADMIN)

    def has_object_permission(self, request, view, obj):
        return _role(request.user) in (User.ROLE_POWER_USER, User.ROLE_ADMIN)


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner (``owner`` or ``created_by``) or admin.

    Works for both ``CampusNetwork`` (``owner``) and ``CampusType``
    (``created_by``); whichever attribute is present is used.
    """

    def has_object_permission(self, request, view, obj):
        if _role(request.user) == User.ROLE_ADMIN:
            return True
        owner = getattr(obj, "owner", None)
        if owner is None:
            owner = getattr(obj, "created_by", None)
        return owner is not None and owner == request.user


class IsOwnerOrTeamMemberOrAdmin(BasePermission):
    """Object-level for networks.

    Full access (read + write): ``power_user`` and ``admin``.
    Read (safe methods): owner, a member of the object's team.
    Write: owner only (team members are read-only).
    """

    def has_object_permission(self, request, view, obj):
        if _role(request.user) in (User.ROLE_POWER_USER, User.ROLE_ADMIN):
            return True
        is_owner = getattr(obj, "owner", None) == request.user
        if request.method in SAFE_METHODS:
            if is_owner:
                return True
            team = getattr(obj, "team", None)
            return bool(
                team is not None and team.members.filter(pk=request.user.pk).exists()
            )
        return is_owner


class IsAdminOrManagesNonAdminUser(BasePermission):
    """Object-level for user records.

    Admin manages any user. A ``power_user`` (a "junior admin") manages any
    **non-admin** user — never an ``admin`` account. Role-value ceilings (a power
    user may not grant the ``admin`` role) are enforced in the view.
    """

    def has_permission(self, request, view):
        return _role(request.user) in (User.ROLE_POWER_USER, User.ROLE_ADMIN)

    def has_object_permission(self, request, view, obj):
        role = _role(request.user)
        if role == User.ROLE_ADMIN:
            return True
        if role == User.ROLE_POWER_USER:
            return getattr(obj, "role", None) != User.ROLE_ADMIN
        return False
