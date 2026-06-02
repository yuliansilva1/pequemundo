from django import template

register = template.Library()


@register.filter
def chile_currency(value, arg=None):
    """Formatea estrictamente un número como moneda chilena sin decimales."""
    try:
        v = float(value or 0)
    except Exception:
        return value

    # Forzamos siempre a 0 decimales, ignorando cualquier otra regla
    s = f"{v:,.0f}"

    # s like '1,234.56' -> convert to '1.234,56'
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"${s}"
