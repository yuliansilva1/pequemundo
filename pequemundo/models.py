from django.db import models

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True, db_column='id_usuario')
    id_rol = models.IntegerField(db_column='id_rol', blank=True, null=True)
    nombre = models.CharField(max_length=150, db_column='nombre')
    apellido = models.CharField(max_length=150, db_column='apellido', blank=True, null=True)
    email = models.CharField(max_length=254, db_column='email', blank=True, null=True)
    contrasena = models.CharField(max_length=128, db_column='contrasena')
    telefono = models.CharField(max_length=50, db_column='telefono', blank=True, null=True)
    direccion = models.CharField(max_length=255, db_column='direccion', blank=True, null=True)
    activo = models.CharField(max_length=1, db_column='activo', default='1')
    fecha_registro = models.DateTimeField(db_column='fecha_registro', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuario'

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True, db_column='id_categoria')
    nombre = models.CharField(max_length=100, db_column='nombre')
    descripcion = models.CharField(max_length=200, db_column='descripcion', blank=True, null=True)
    activo = models.CharField(max_length=1, db_column='activo', default='1')

    class Meta:
        managed = False
        db_table = 'categoria'

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True, db_column='id_producto')
    id_categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, db_column='id_categoria')
    nombre = models.CharField(max_length=200, db_column='nombre')
    descripcion = models.CharField(max_length=200, db_column='descripcion', blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, db_column='precio')
    stock = models.IntegerField(default=0, db_column='stock')
    imagen_url = models.CharField(max_length=500, db_column='imagen_url', blank=True, null=True)
    activo = models.CharField(max_length=1, db_column='activo', default='1')
    fecha_creacion = models.DateTimeField(db_column='fecha_creacion', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'producto'

    def __str__(self):
        return self.nombre