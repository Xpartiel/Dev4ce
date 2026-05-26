# Postman · Luciérnagas 2026

## Importar
1. Abre Postman → **Import** → arrastra los dos archivos:
   - `Luciernagas2026.postman_collection.json`  (colección)
   - `Luciernagas2026.local.postman_environment.json`  (entorno local)
2. En la esquina superior derecha, selecciona el entorno **Luciernagas · Local**.

## Orden recomendado de ejecución
```
1 · Autenticación
   ├─ RF-01 Registro
   ├─ RF-01.2 duplicado (debe fallar)
   ├─ RF-01.3 password débil (debe fallar)
   ├─ RF-02 Login                ← guarda sesión automáticamente
   └─ RF-02.4 login inválido

2 · Parques  (necesitas usuario admin — créalo con createsuperuser)
   ├─ RF-04/05 Listar
   ├─ RF-10.1 Crear              ← guarda parque_id
   ├─ RF-10.2 Editar
   ├─ RF-05  Detalle
   └─ RF-10.3 Eliminar

3 · Reservaciones
   ├─ RF-06 Crear (válida)       ← guarda reserva_id
   ├─ RF-06.2 fuera temporada
   ├─ RF-06.3 incluye martes
   ├─ RF-06.4 cabaña no disponible
   ├─ RF-06.5 sin cupo
   ├─ RF-08 Mis reservaciones
   ├─ RF-09 Cancelar
   └─ RF-11 Vista admin
```

## Runner (corre toda la suite)
Postman → **Runner** → Selecciona la colección → **Run**.
Cada request tiene aserciones en JS; al final ves el reporte de pasados/fallados.

## CLI con Newman (para CI)
```bash
npm i -g newman
newman run postman/Luciernagas2026.postman_collection.json \
       -e postman/Luciernagas2026.local.postman_environment.json
```
