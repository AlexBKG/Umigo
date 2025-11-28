from django import template

register = template.Library()

@register.filter('inGroup')
def inGroup(user, group_name):
    return user.groups.filter(name=group_name).exists()