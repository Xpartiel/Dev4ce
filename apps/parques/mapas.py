"""
Construcción del mapa de parques con Folium.

Se usa tanto en la landing (parques.views.landing) como en el mapa del
cliente (reservaciones.views.mapa_cliente): ambos comparten esta base.

Nota: el CSS y el JS viven aquí (y no en styles.css) porque Folium genera
el mapa dentro de un <iframe> aparte que NO carga los estilos del sitio;
hay que inyectarlos dentro del propio mapa.
"""

import folium
from django.urls import reverse


# Colores por disponibilidad
_COLORES = {
    "libre":         {"core": "#FFC857", "glow": "rgba(255,200,87,.95)", "pulse": "rgba(255,200,87,.5)"},
    "pocos":         {"core": "#FF8C42", "glow": "rgba(255,140,66,.95)", "pulse": "rgba(255,140,66,.5)"},
    "agotado":       {"core": "#9B2226", "glow": "rgba(155,34,38,.80)",  "pulse": "rgba(155,34,38,.4)"},
    "mantenimiento": {"core": "#5B8DB8", "glow": "rgba(91,141,184,.80)", "pulse": "rgba(91,141,184,.4)"},
}


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
  .leaflet-popup-content-wrapper {
    background:#050810; color:#F5EFE0;
    border:1px solid rgba(255,200,87,.35); border-radius:10px;
  }
  .leaflet-popup-tip { background:#050810; }

  .mapa-leyenda {
    position:absolute; bottom:28px; left:12px; z-index:999;
    background:rgba(5,8,16,.82); color:#F5EFE0;
    border:1px solid rgba(255,200,87,.25); border-radius:8px;
    padding:10px 14px; font-family:'JetBrains Mono',monospace; font-size:12px;
    pointer-events:none;
  }
  .mapa-leyenda-item { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
  .mapa-leyenda-item:last-child { margin-bottom:0; }
  .mapa-leyenda-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
</style>
"""

LEYENDA_HTML = """
<div class="mapa-leyenda">
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
    """JS que cambia la base del mapa cuando la página cambia de tema."""
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
          if (light) {{ mapa.removeLayer(noche); dia.addTo(mapa); }}
          else       {{ mapa.removeLayer(dia);   noche.addTo(mapa); }}
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


def _firefly_icon(indice, estado="libre"):
    """DivIcon con color según disponibilidad del parque."""
    delay   = (indice % 6) * 0.35
    colores = _COLORES.get(estado, _COLORES["libre"])
    html = (
        f'<div class="firefly-pin">'
        f'<span class="firefly-glow" style="'
        f'background:radial-gradient(circle,{colores["pulse"]} 0%,rgba(0,0,0,0) 70%);'
        f'animation-delay:{delay}s"></span>'
        f'<span class="firefly-core" style="'
        f'background:{colores["core"]};box-shadow:0 0 8px 2px {colores["glow"]};'
        f'animation-delay:{delay}s"></span>'
        f'</div>'
    )
    return folium.DivIcon(html=html, icon_size=(22, 22), icon_anchor=(11, 11))


def construir_mapa(parques, *, con_enlaces=True, zoom=11):
    """
    Devuelve el HTML (iframe) de un mapa Folium con un marcador-luciérnaga
    por cada parque. Se adapta al tema claro/oscuro de la página.
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
            enlace = (
                f'<a href="{url}" target="_top" style="color:#FFC857;font-weight:bold">'
                f'Ver detalles →</a>'
            )
        else:
            enlace = (
                f'<a href="{login_url}" target="_top" '
                f'style="color:#FFC857;font-weight:bold">'
                f'Iniciar sesión →</a>'
            )

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
            f'<strong style="color:#FFC857">{parque.nombre}</strong><br>'
            f'<span style="color:{estado_color};font-size:11px">{estado_label}</span><br><br>'
            f'Camping: <strong>${parque.precio_camping}/noche</strong><br>'
            f'{enlace}'
            f'</div>'
        )

        folium.Marker(
            location=[lat, lng],
            tooltip=parque.nombre,
            popup=folium.Popup(popup_html, max_width=240),
            icon=_firefly_icon(i, estado),
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

    return mapa._repr_html_()