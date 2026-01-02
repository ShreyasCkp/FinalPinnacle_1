from django import template

register = template.Library()

@register.filter
def get_perm(perms, form_action):
    form, action = form_action.split('|')
    return perms.get(form, {}).get(action, False)


@register.simple_tag
def get_value(perms, form, action):
    return perms.get(form, {}).get(action, False)


@register.filter
def get_item(queryset, pk):
    try:
        return queryset.get(pk=pk)
    except:
        return ''


@register.filter(name='add_class')
def add_class(field, css):
    """Add CSS class to form field"""
    return field.as_widget(attrs={"class": css})