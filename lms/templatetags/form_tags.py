
# from django import template

# register = template.Library()

# @register.filter(name='add_class')
# def add_class(field, css):
#     return field.as_widget(attrs={"class": css})



from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})


from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})

@register.filter(name='dict_get')
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None

# #student assignmnet view the faculty
# from django import template
# register = template.Library()

# @register.filter
# def get_item(dictionary, key):
#     return dictionary.get(key)


