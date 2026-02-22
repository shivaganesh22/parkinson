from django import template

register = template.Library()


@register.filter
def get_by_index(lst, index):
    """Get item from list by index."""
    try:
        return lst[int(index)]
    except (IndexError, ValueError, TypeError):
        return None


@register.filter
def format_feature_value(value):
    """Format feature value to 4 decimal places if it's a number."""
    try:
        return round(float(value), 4)
    except (ValueError, TypeError):
        return value
