
# attendence/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def prettify_label(value):
    """Replace underscores with spaces and capitalize each word."""
    return value.replace('_', ' ').title()

