# core/models.py
from django.db import models
from django.contrib.auth.models import User

# Define los Niveles de Acceso
NIVEL_ACCESO_CHOICES = (
    (1, 'Administrador'),
    (2, 'Responsable'),
    (3, 'Jefe Almacén'),
)

class PerfilUsuario(models.Model):
    """Extiende el modelo User de Django para añadir campos de perfil."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nivel_acceso = models.IntegerField(
        choices=NIVEL_ACCESO_CHOICES, 
        default=3, 
        verbose_name="Nivel de Acceso"
    )
    numero_empleado = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Número de Empleado"
    )

    def __str__(self):
        return f"Perfil de {self.user.username} - Nivel {self.get_nivel_acceso_display()}"