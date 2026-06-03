"""
Construcción del mapa de parques con Folium.
"""

import folium
from django.urls import reverse

UMBRAL_ZOOM_ETIQUETAS = 12


# Colores por disponibilidad
_COLORES = {
    "libre":         {"core": "#FFC857", "glow": "rgba(255,200,87,.95)", "pulse": "rgba(255,200,87,.5)"},
    "pocos":         {"core": "#FF8C42", "glow": "rgba(255,140,66,.95)", "pulse": "rgba(255,140,66,.5)"},
    "agotado":       {"core": "#9B2226", "glow": "rgba(155,34,38,.80)",  "pulse": "rgba(155,34,38,.4)"},
    "mantenimiento": {"core": "#5B8DB8", "glow": "rgba(91,141,184,.80)", "pulse": "rgba(91,141,184,.4)"},
}

# Folium solo permite personalizar los pins con iconos predefinidos o con DivIcon (HTML+CSS).
ESTILO_MAPA = """
<style>
  .firefly-pin { position:relative; width:22px; height:22px; }
  .firefly-core {
    position:absolute; left:50%; top:50%; width:9px; height:9px;
    margin:-4.5px 0 0 -4.5px; border-radius:50%;
    animation: ff-blink 2.4s ease-in-out infinite;
  }
  .firefly-glow {
    position:absolute; left:50%; top:50%; width:26px; height:26px;
    margin:-13px 0 0 -13px; border-radius:50%;
    animation: ff-pulse 2.4s ease-in-out infinite;
  }
  @keyframes ff-blink { 0%,100%{opacity:.55} 50%{opacity:1} }
  @keyframes ff-pulse { 0%,100%{transform:scale(.7);opacity:.45} 50%{transform:scale(1.4);opacity:.85} }

  /* Etiqueta con el nombre del parque: OCULTA por defecto; se muestra solo
     cuando el JS agrega la clase .show-labels (al superar cierto zoom). */
  .firefly-label {
    display:none;
    position:absolute; left:18px; top:50%; transform:translateY(-50%);
    white-space:nowrap;
    font-family:'JetBrains Mono',monospace; font-size:11.5px; font-weight:600;
    color:#FFF3D6;
    background:rgba(5,8,16,.82);
    padding:2px 7px; border-radius:7px;
    border:1px solid rgba(255,200,87,.45);
    box-shadow:0 1px 4px rgba(0,0,0,.55);
    text-shadow:0 1px 2px rgba(0,0,0,.9);
    pointer-events:none;
  }
  .show-labels .firefly-label { display:block; }

  /* Nombre al pasar el cursor / tocar el pin (tooltip), con el estilo del
     sitio. Útil sobre todo cuando estás alejado y las etiquetas están ocultas. */
  .leaflet-tooltip {
    background:rgba(5,8,16,.88); color:#FFF3D6;
    border:1px solid rgba(255,200,87,.5); border-radius:7px;
    padding:3px 9px; box-shadow:0 2px 6px rgba(0,0,0,.5);
    font-family:'JetBrains Mono',monospace; font-weight:600; font-size:12px;
    white-space:nowrap;
  }
  .leaflet-tooltip::before { display:none; }   /* quita la flechita */

  /* Popup (al hacer clic en el pin) */
  .leaflet-popup-content-wrapper {
    background:#050810; color:#F5EFE0;
    border:1px solid rgba(255,200,87,.35); border-radius:10px;
  }
  .leaflet-popup-tip { background:#050810; }
  .fp-nombre { color:#FFC857; }
  .fp-link   { color:#FFC857; font-weight:bold; }

  /* Leyenda */
  .mapa-leyenda {
    position:absolute; top:12px; right:12px; z-index:999;
    background:rgba(5,8,16,.86); color:#F5EFE0;
    border:1px solid rgba(255,200,87,.35); border-radius:8px;
    padding:10px 14px; font-family:'JetBrains Mono',monospace; font-size:12px;
    box-shadow:0 2px 10px rgba(0,0,0,.5);
    pointer-events:none;
  }
  .mapa-leyenda-titulo {
    font-weight:600; color:#FFC857; margin-bottom:7px;
    font-size:11px; letter-spacing:.05em; text-transform:uppercase;
  }
  .mapa-leyenda-item { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
  .mapa-leyenda-item:last-child { margin-bottom:0; }
  .mapa-leyenda-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }

  /* ===== MODO CLARO: adapta el chrome del mapa (en vez de quedar todo negro) ===== */
  .map-light .firefly-label {
    color:#3a2e16; background:rgba(255,255,255,.92);
    border-color:#E0A93B; text-shadow:none; box-shadow:0 1px 4px rgba(0,0,0,.18);
  }
  .map-light .leaflet-tooltip {
    background:rgba(255,255,255,.96); color:#3a2e16;
    border-color:#E0A93B; box-shadow:0 2px 6px rgba(0,0,0,.18);
  }
  .map-light .leaflet-popup-content-wrapper {
    background:#FFFDF7; color:#2c2415; border-color:#E0A93B;
  }
  .map-light .leaflet-popup-tip { background:#FFFDF7; }
  .map-light .fp-nombre,
  .map-light .fp-link { color:#B5791B; }
  .map-light .mapa-leyenda {
    background:rgba(255,253,247,.95); color:#2c2415;
    border-color:#E0A93B; box-shadow:0 2px 10px rgba(0,0,0,.18);
  }
  .map-light .mapa-leyenda-titulo { color:#B5791B; }
</style>
"""

LEYENDA_HTML = """
<div class="mapa-leyenda">
  <div class="mapa-leyenda-titulo">Disponibilidad</div>
  <div class="mapa-leyenda-item">
    <span class="mapa-leyenda-dot" style="background:#FFC857;box-shadow:0 0 5px rgba(255,200,87,.8)"></span>
    Disponible
  </div>
  <div class="mapa-leyenda-item">
    <span class="mapa-leyenda-dot" style="background:#FF8C42;box-shadow:0 0 5px rgba(255,140,66,.8)"></span>
    Pocos lugares
  </div>
  <div class="mapa-leyenda-item">
    <span class="mapa-leyenda-dot" style="background:#9B2226;box-shadow:0 0 5px rgba(155,34,38,.7)"></span>
    Agotado
  </div>
</div>
"""


def _puente_tema(map_name, noche_name, dia_name):
    """
    JS que cambia la base del mapa y el estilo del chrome (tooltip/popup/leyenda)
    cuando la página cambia de tema claro/oscuro.
    """
    return f"""
    <script>
      window.addEventListener('load', function () {{
        var mapa  = {map_name};
        var noche = {noche_name};
        var dia   = {dia_name};
        function aplicar() {{
          var light = false;
          try {{
            light = window.parent.document.documentElement
                      .getAttribute('data-theme') === 'light';
          }} catch (e) {{}}
          if (light) {{
            mapa.removeLayer(noche); dia.addTo(mapa);
            document.documentElement.classList.add('map-light');
          }} else {{
            mapa.removeLayer(dia); noche.addTo(mapa);
            document.documentElement.classList.remove('map-light');
          }}
        }}
        aplicar();
        try {{
          new MutationObserver(aplicar).observe(
            window.parent.document.documentElement,
            {{ attributes: true, attributeFilter: ['data-theme'] }}
          );
        }} catch (e) {{}}
      }});
    </script>
    """


def _firefly_icon(indice, estado="libre", nombre=""):
    """
    DivIcon (pin luciérnaga) con color según disponibilidad. Incluye la etiqueta
    con el nombre, que el CSS muestra solo cuando hay suficiente zoom.
    """
    delay   = (indice % 6) * 0.35
    colores = _COLORES.get(estado, _COLORES["libre"])
    etiqueta = f'<span class="firefly-label">{nombre}</span>' if nombre else ""
    html = (
        f'<div class="firefly-pin">'
        f'<span class="firefly-glow" style="'
        f'background:radial-gradient(circle,{colores["pulse"]} 0%,rgba(0,0,0,0) 70%);'
        f'animation-delay:{delay}s"></span>'
        f'<span class="firefly-core" style="'
        f'background:{colores["core"]};box-shadow:0 0 8px 2px {colores["glow"]};'
        f'animation-delay:{delay}s"></span>'
        f'{etiqueta}'
        f'</div>'
    )
    return folium.DivIcon(html=html, icon_size=(22, 22), icon_anchor=(11, 11))


def construir_mapa(parques, *, con_enlaces=True, zoom=11):
    """
    Devuelve el HTML (iframe) de un mapa Folium con un marcador-luciérnaga por
    parque. Los nombres aparecen como etiquetas al acercar el zoom (umbral
    UMBRAL_ZOOM_ETIQUETAS); al pasar/tocar un pin sale el nombre (tooltip) y al
    hacer clic el detalle (popup). Se adapta al tema claro/oscuro de la página.
    """
    mapa = folium.Map(
        location=[19.42, -98.60],
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
    )

    noche = folium.TileLayer("CartoDB dark_matter", name="Noche", control=False)
    dia   = folium.TileLayer("CartoDB positron",    name="Dia",   control=False)
    noche.add_to(mapa)
    dia.add_to(mapa)

    login_url = reverse("login")

    coords = []
    for i, parque in enumerate(parques):
        lat, lng = float(parque.latitud), float(parque.longitud)
        coords.append((lat, lng))

        estado = parque.disponibilidad_global

        if con_enlaces:
            url    = reverse("detalle_parque", args=[parque.pk])
            enlace = f'<a class="fp-link" href="{url}" target="_top">Ver detalles →</a>'
        else:
            enlace = f'<a class="fp-link" href="{login_url}" target="_top">Iniciar sesión →</a>'

        estado_label = {
            "libre":         "Disponible",
            "pocos":         "Pocos lugares",
            "agotado":       "Agotado",
            "mantenimiento": "Mantenimiento",
        }.get(estado, "Disponible")

        estado_color = {
            "libre":         "#4CAF7D",
            "pocos":         "#FF8C42",
            "agotado":       "#C85A5A",
            "mantenimiento": "#5B8DB8",
        }.get(estado, "#4CAF7D")

        popup_html = (
            f'<div style="font-family:\'JetBrains Mono\',monospace;min-width:170px">'
            f'<strong class="fp-nombre">{parque.nombre}</strong><br>'
            f'<span style="color:{estado_color};font-size:11px">{estado_label}</span><br><br>'
            f'Camping: <strong>${parque.precio_camping}/noche</strong><br>'
            f'{enlace}'
            f'</div>'
        )

        folium.Marker(
            location=[lat, lng],
            tooltip=parque.nombre,
            popup=folium.Popup(popup_html, max_width=240),
            icon=_firefly_icon(i, estado, parque.nombre),
        ).add_to(mapa)

    if coords:
        lats = [c[0] for c in coords]
        lngs = [c[1] for c in coords]
        mapa.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]])

    mapa.get_root().header.add_child(folium.Element(ESTILO_MAPA))
    mapa.get_root().html.add_child(folium.Element(LEYENDA_HTML))
    mapa.get_root().html.add_child(
        folium.Element(_puente_tema(mapa.get_name(), noche.get_name(), dia.get_name()))
    )

    # Muestra las etiquetas con el nombre solo a partir de cierto zoom (para que
    # no se encimen cuando el mapa está alejado y los parques se ven juntos).
    mapa.get_root().html.add_child(folium.Element(
        f"<script>window.addEventListener('load', function () {{"
        f"  var m = {mapa.get_name()};"
        f"  function etiquetas() {{"
        f"    if (m.getZoom() >= {UMBRAL_ZOOM_ETIQUETAS})"
        f"      document.documentElement.classList.add('show-labels');"
        f"    else document.documentElement.classList.remove('show-labels');"
        f"  }}"
        f"  m.on('zoomend', etiquetas); etiquetas();"
        f"}});</script>"
    ))

    # Desactiva el zoom con la rueda del ratón: así al hacer scroll se mueve la
    # página y el mapa no "atrapa" el desplazamiento. El zoom sigue disponible
    # con los botones + / - y el doble clic.
    mapa.get_root().html.add_child(folium.Element(
        f"<script>window.addEventListener('load', function () {{"
        f" try {{ {mapa.get_name()}.scrollWheelZoom.disable(); }} catch (e) {{}}"
        f" }});</script>"
    ))

    return mapa._repr_html_()