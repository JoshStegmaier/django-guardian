from __future__ import unicode_literals
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from guardian.compat import unicode, user_model_label
from guardian.ctypes import get_content_type
from guardian.managers import GroupObjectPermissionManager, UserObjectPermissionManager

try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey


class BaseObjectPermission(models.Model):
    """
    Abstract ObjectPermission class. Actual class should additionally define
    a ``content_object`` field and either ``user`` or ``group`` field.
    """
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __unicode__(self):
        return '%s | %s | %s' % (
            unicode(self.content_object),
            unicode(getattr(self, 'user', False) or self.group),
            unicode(self.permission.codename))

    def save(self, *args, **kwargs):
        content_type = get_content_type(self.content_object)
        if content_type != self.permission.content_type:
            raise ValidationError("Cannot persist permission not designed for "
                                  "this class (permission's type is %r and object's type is %r)"
                                  % (self.permission.content_type, content_type))
        return super(BaseObjectPermission, self).save(*args, **kwargs)


class BaseGenericObjectPermission(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    #object_pk = models.CharField(_('object ID'), max_length=255)
    object_pk = models.PositiveIntegerField()
    content_object = GenericForeignKey(fk_field='object_pk')

    class Meta:
        abstract = True


class UserObjectPermissionBase(BaseObjectPermission):
    """
    **Manager**: :manager:`UserObjectPermissionManager`
    """
    user = models.ForeignKey(user_model_label, on_delete=models.CASCADE)

    objects = UserObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ['user', 'permission', 'content_object']


class UserObjectPermission(UserObjectPermissionBase, BaseGenericObjectPermission):

    class Meta:
        unique_together = ['user', 'permission', 'object_pk']


class GroupObjectPermissionBase(BaseObjectPermission):
    """
    **Manager**: :manager:`GroupObjectPermissionManager`
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    objects = GroupObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ['group', 'permission', 'content_object']


class GroupObjectPermission(GroupObjectPermissionBase, BaseGenericObjectPermission):

    class Meta:
        unique_together = ['group', 'permission', 'object_pk']


setattr(Group, 'add_obj_perm',
        lambda self, perm, obj: GroupObjectPermission.objects.assign_perm(perm, self, obj))
setattr(Group, 'del_obj_perm',
        lambda self, perm, obj: GroupObjectPermission.objects.remove_perm(perm, self, obj))
