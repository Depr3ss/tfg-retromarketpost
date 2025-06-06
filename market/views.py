from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Producto, Carrito, CarritoItem, Pedido, LineaPedido, Categoria
from .forms import ProductoForm
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import RegistroUsuarioForm, ProductoForm
from django.db.models import Q

@login_required
def lista_productos(request):
    """
    Muestra los productos que ha subido el usuario actual.
    Solo pueden acceder usuarios logueados.
    """
    productos = Producto.objects.filter(propietario=request.user)
    return render(request, 'market/lista_productos.html', {'productos': productos})

@login_required
def crear_producto(request):
    """
    Permite al usuario crear (subir) un nuevo producto.
    Si es GET, muestra el formulario.
    Si es POST, guarda el producto si el formulario es válido.
    """
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.propietario = request.user
            producto.save()
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'market/crear_producto.html', {'form': form})

@login_required
def editar_producto(request, pk):
    """
    Permite editar un producto propio del usuario.
    Si es GET, muestra el formulario con los datos actuales.
    Si es POST, guarda los cambios.
    """
    producto = get_object_or_404(Producto, pk=pk, propietario=request.user)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'market/editar_producto.html', {'form': form})

@login_required
def eliminar_producto(request, pk):
    """
    Permite eliminar un producto del usuario.
    Pide confirmación antes de borrar.
    """
    producto = get_object_or_404(Producto, pk=pk, propietario=request.user)
    if request.method == 'POST':
        producto.delete()
        return redirect('lista_productos')
    return render(request, 'market/eliminar_producto.html', {'producto': producto})

class CatalogoPublicoView(ListView):
    """
    Vista pública del catálogo de productos.
    Permite buscar por nombre o descripción y filtrar por categoría.
    """
    model = Producto
    template_name = 'market/catalogo_publico.html'
    context_object_name = 'productos'
    paginate_by = 15

    def get_queryset(self):
        """
        Devuelve los productos filtrados por búsqueda o categoría si se aplican.
        """
        query = self.request.GET.get('q')
        categoria_id = self.request.GET.get('categoria')
        productos = Producto.objects.all()

        if query:
            productos = productos.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))

        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)

        return productos

    def get_context_data(self, **kwargs):
        """
        Agrega datos extra al contexto, como el modo claro/oscuro y la categoría seleccionada.
        """
        context = super().get_context_data(**kwargs)
        context['modo'] = self.request.GET.get('modo', 'claro')
        context['categorias'] = Categoria.objects.all()
        context['categoria_seleccionada'] = int(self.request.GET.get('categoria')) if self.request.GET.get('categoria') else None
        return context

def registro(request):
    """
    Registra un nuevo usuario.
    Si el formulario es válido, lo loguea automáticamente y lo redirige al catálogo.
    """
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registro exitoso. ¡Bienvenido!")
            return redirect('catalogo_publico')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'market/registro.html', {'form': form})

def detalle_producto(request, pk):
    """
    Muestra los detalles de un producto específico.
    También sugiere productos relacionados de la misma categoría.
    """
    producto = get_object_or_404(Producto, pk=pk)
    relacionados = Producto.objects.filter(categoria=producto.categoria).exclude(pk=pk)[:3]
    return render(request, 'market/detalle_producto.html', {
        'producto': producto,
        'relacionados': relacionados
    })

@login_required
def agregar_al_carrito(request, producto_id):
    """
    Agrega un producto al carrito del usuario.
    Si ya estaba, aumenta la cantidad si hay stock.
    """
    producto = get_object_or_404(Producto, id=producto_id)

    if producto.stock < 1:
        messages.error(request, f"Lo sentimos, el producto '{producto.nombre}' está agotado.")
        return redirect('catalogo_publico')

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user, completado=False)

    item, creado = CarritoItem.objects.get_or_create(carrito=carrito, producto=producto)
    if not creado:
        if producto.stock >= item.cantidad + 1:
            item.cantidad += 1
            item.save()
        else:
            messages.warning(request, f"Solo quedan {producto.stock} unidades de '{producto.nombre}'.")
    else:
        item.save()

    return redirect('ver_carrito')

@login_required
def ver_carrito(request):
    """
    Muestra el carrito actual del usuario con el total a pagar.
    """
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user, completado=False)
    total = carrito.total()
    return render(request, 'market/carrito.html', {'carrito': carrito, 'total': total})

@login_required
def eliminar_item_carrito(request, item_id):
    """
    Elimina un producto específico del carrito del usuario.
    """
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    item.delete()
    return redirect('ver_carrito')

@login_required
def vaciar_carrito(request):
    """
    Elimina todos los productos del carrito actual del usuario.
    """
    carrito = get_object_or_404(Carrito, usuario=request.user, completado=False)
    carrito.items.all().delete()
    return redirect('ver_carrito')

@login_required
def checkout(request):
    """
    Muestra y procesa el formulario de compra.
    Si todo está correcto, crea el pedido, descuenta stock y marca el carrito como completado.
    """
    carritos = Carrito.objects.filter(usuario=request.user, completado=False).order_by('-id')
    if carritos.count() > 1:
        for carrito in carritos[1:]:
            carrito.delete()

    carrito = carritos.first()
    if not carrito or not carrito.items.exists():
        return redirect('ver_carrito')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        email = request.POST.get('email') or request.user.email

        if not nombre or not direccion or not email:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'market/checkout.html', {
                'carrito': carrito,
                'total': carrito.total()
            })

        pedido = Pedido.objects.create(
            usuario=request.user,
            nombre=nombre,
            direccion=direccion,
            email=email
        )

        for item in carrito.items.all():
            LineaPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                cantidad=item.cantidad
            )
            item.producto.stock -= item.cantidad
            item.producto.save()

        carrito.completado = True
        carrito.save()

        return redirect('checkout_exito', pedido_id=pedido.id)

    return render(request, 'market/checkout.html', {
        'carrito': carrito,
        'total': carrito.total()
    })

@login_required
def checkout_exito(request, pedido_id):
    """
    Muestra una página de éxito después de completar un pedido.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'market/checkout_exito.html', {'pedido': pedido})
