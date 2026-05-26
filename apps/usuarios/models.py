"""
Vista 1 del diagrama de clases — Autenticación.
Modelos: Persona, Contraseña (gestionada por Django), Perfil (AUTH_USER_MODEL).
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# ---------------------------------------------------------------
# ENUM Rol
# ---------------------------------------------------------------
class Rol(models.TextChoices):
    CLIENTE       = "CLIENTE",       "Cliente"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


# ---------------------------------------------------------------
# Persona — PII (LFPDPPP / RNF-02)
# ---------------------------------------------------------------
class Persona(models.Model):
    nombre = models.CharField(max_length=80)
    apellido_paterno = models.CharField(max_length=80)
    apellido_materno = models.CharField(max_length=80, blank=True)
    email = models.EmailField(unique=True)        # RF-01.2
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Persona"
        verbose_name_plural = "Personas"

    def __str__(self):
        return self.nombre_completo()

    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}".strip()


# ---------------------------------------------------------------
# Perfil
# AUTH_USER_MODEL (datos públicos + rol + auth)
# La "Contraseña" del diagrama vive en password_hash (manejado por Django).
# ---------------------------------------------------------------
class PerfilManager(BaseUserManager):
    """Manager estándar; el Factory Method vive en managers.PerfilFactory."""

    def create_user(self, email, password, **extra):
        if not email:
            raise ValueError("El correo electrónico es obligatorio")
        email = self.normalize_email(email)
        persona = extra.pop("persona", None)
        if persona is None:
            persona = Persona.objects.create(
                email=email,
                nombre=extra.pop("nombre", ""),
                apellido_paterno=extra.pop("apellido_paterno", ""),
                apellido_materno=extra.pop("apellido_materno", ""),
            )
        perfil = self.model(persona=persona, email=email, **extra)
        perfil.set_password(password)   # bcrypt — RF-01.4
        perfil.save(using=self._db)
        return perfil

    def create_superuser(self, email, password, **extra):
        extra.setdefault("rol", Rol.ADMINISTRADOR)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class Perfil(AbstractBaseUser, PermissionsMixin):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name="perfil")
    email = models.EmailField(unique=True)
    nick_name = models.CharField(max_length=60, blank=True)
    foto_perfil = models.ImageField(upload_to="perfiles/", blank=True, null=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CLIENTE)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    objects = PerfilManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"{self.email} ({self.rol})"

    def es_admin(self)   -> bool: return self.rol == Rol.ADMINISTRADOR
    def es_cliente(self) -> bool: return self.rol == Rol.CLIENTE


# ---------------------------------------------------------------
# AuditLog — registro de intentos de login (Proxy / RNF-02)
# ---------------------------------------------------------------
class AuditLog(models.Model):
    correo = models.EmailField()
    exito = models.BooleanField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
