

from django import template

register = template.Library()
 
@register.filter(name='add_class')

def add_class(field, css):

    return field.as_widget(attrs={"class": css})
 
@register.filter(name='attr')

def attr(field, attr_string):

    key, value = attr_string.split('=')

    return field.as_widget(attrs={key: value})

 