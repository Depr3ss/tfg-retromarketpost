from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Producto(models.Model):
    """
    Representa un producto que se vende en la tienda.
    Tiene nombre, descripción, precio, imagen, fecha de publicación,
    propietario (usuario que lo publicó), categoría y stock disponible.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    propietario = models.ForeignKey(User, on_delete=models.CASCADE)
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.PositiveIntegerField(default=1)

    def __str__(self):
        """Muestra el nombre del producto cuando se imprime o se ve en el admin."""
        return self.nombre

class Categoria(models.Model):
    """
    Guarda las categorías de los productos (ej: Electrónica, Ropa, etc.).
    El nombre es único para evitar duplicados.
    """
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        """Define cómo se muestra el nombre en singular y plural en el admin de Django."""
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        """Muestra el nombre de la categoría."""
        return self.nombre

class Carrito(models.Model):
    """
    Representa el carrito de compras de un usuario.
    Puede tener muchos productos y puede estar 'completado' o no.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    completado = models.BooleanField(default=False)

    class Meta:
        """
        Evita que un usuario tenga más de un carrito sin completar al mismo tiempo.
        """
        constraints = [
            models.UniqueConstraint(
                fields=['usuario'],
                condition=models.Q(completado=False),
                name='unique_carrito_por_usuario_no_completado'
            )
        ]

    def carrito_count(request):
        """
        Devuelve la cantidad de items en el carrito del usuario actual.
        Es útil para mostrar ese número en la barra de navegación, por ejemplo.
        """
        if request.user.is_authenticated:
            try:
                carrito = Carrito.objects.get(usuario=request.user, completado=False)
                return {'carrito_count': carrito.items.count()}
            except Carrito.DoesNotExist:
                return {'carrito_count': 0}
        return {'carrito_count': 0}

    def total(self):
        """
        Calcula el total del carrito sumando el total de cada item.
        """
        return sum(item.total() for item in self.items.all())

    def __str__(self):
        """Muestra algo como 'Carrito de juan123'."""
        return f"Carrito de {self.usuario.username}"

class CarritoItem(models.Model):
    """
    Representa un producto dentro del carrito.
    Guarda el producto, a qué carrito pertenece y la cantidad.
    """
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def total(self):
        """
        Calcula el precio total de este item (producto * cantidad).
        """
        return self.producto.precio * self.cantidad

    def __str__(self):
        """Ejemplo: 'Camiseta x2'."""
        return f"{self.producto.nombre} x{self.cantidad}"

class Pedido(models.Model):
    """
    Representa un pedido realizado por un usuario después de completar su carrito.
    Guarda los datos de envío, contacto y si ya fue completado.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    email = models.EmailField()
    creado = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)

    def total(self):
        """
        Suma el subtotal de todas las líneas del pedido.
        """
        return sum(linea.subtotal() for linea in self.lineaspedido.all())

class LineaPedido(models.Model):
    """
    Representa cada producto dentro de un pedido.
    Guarda el producto, el pedido al que pertenece y cuántos se compraron.
    """
    pedido = models.ForeignKey(Pedido, related_name='lineaspedido', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        """
        Calcula el precio total por esta línea del pedido.
        """
        return self.cantidad * self.producto.precio
