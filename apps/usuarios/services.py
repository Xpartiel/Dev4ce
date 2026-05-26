"""
Proxy de protección — ValidadorInicioSesion (RF-02).
Aplica rate-limit + auditoría antes de delegar en el verificador real.
"""
from django.contrib.auth import authenticate
from django.core.cache import cache
from .models import AuditLog, Perfil


class ValidadorInicioSesion:
    """Patrón Proxy."""

    MAX_INTENTOS = 5
    VENTANA_SEG  = 60 * 5     # 5 minutos

    def __init__(self, correo: str, password: str, ip: str | None = None):
        self.correo   = correo.strip().lower()
        self.password = password
        self.ip       = ip

    # -------------------------- API pública --------------------------
    def validar(self) -> Perfil | None:
        if self._rate_limit_excedido():
            self._registrar_fallo()
            return None

        perfil = authenticate(username=self.correo, password=self.password)
        if perfil is None:
            self._registrar_fallo()
            return None

        AuditLog.objects.create(correo=self.correo, exito=True, ip=self.ip)
        cache.delete(self._cache_key())
        return perfil

    # -------------------------- internos --------------------------
    def _cache_key(self) -> str:
        return f"login_fail:{self.correo}"

    def _rate_limit_excedido(self) -> bool:
        return (cache.get(self._cache_key()) or 0) >= self.MAX_INTENTOS

    def _registrar_fallo(self) -> None:
        key = self._cache_key()
        cache.set(key, (cache.get(key) or 0) + 1, self.VENTANA_SEG)
        AuditLog.objects.create(correo=self.correo, exito=False, ip=self.ip)
