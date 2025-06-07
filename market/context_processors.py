def carrito_count(request):
    """
    Este context processor permite mostrar cuántos productos hay en el carrito 
    del usuario en cualquier página del sitio (en este caso, header).

    Si el usuario está logueado, busca su carrito que aún no ha sido completado.
    Devuelve un diccionario con la clave 'carrito_count' que indica 
    cuántos items tiene su carrito actual.
    """
    if request.user.is_authenticated:
        from .models import Carrito  
        try:
            carrito = Carrito.objects.get(usuario=request.user, completado=False)
            return {'carrito_count': carrito.items.count()}
        except Carrito.DoesNotExist:
            return {'carrito_count': 0}
    return {'carrito_count': 0}
