import pandas as pd
import holoviews as hv
from holoviews.streams import Selection1D
import geoviews as gv

hv.extension('bokeh')

# Constants
width = 1000
height = 700
DIAS = ('LUNES', 'MARTES', 'MIERCOLES',
        'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO')

# Load data
df_centros = pd.read_csv('data/processed/clusters.csv')
df_points_in_clusters = pd.read_csv('data/processed/points_in_clusters.csv',
                                    parse_dates=['fecha'], dtype={'hora': str})
# empty heatmap data
df_empty = pd.DataFrame(index=DIAS,
                        columns=sorted(df_points_in_clusters.hora.unique()))
df_empty = df_empty.reset_index()
df_empty = (pd.melt(df_empty, id_vars='index')
              .rename(columns={'index': 'dia_semana', 'variable': 'hora'}))

index_to_cluster = {
    i: row.cluster for i, row in enumerate(df_centros.itertuples())
}


def empty_heatmap():
    """Crea un heatmap con datos nulos"""
    heatmap_opts = dict(width=600, height=300, cmap='viridis',
                        colorbar=True, show_title=False, tools=['hover'])
    heatmap = hv.HeatMap(
        df_empty, kdims=['hora', 'dia_semana'], vdims=['value']
    ).options(**heatmap_opts)
    return heatmap


def generar_heatmap(cluster, indice):
    """Genera el heatmap de accidentes de cada cluster"""
    df_heat = (df_points_in_clusters.loc[df_points_in_clusters.cluster == cluster]
               .groupby(['dia_semana', 'hora'], as_index=False)
               .cluster.count())
    df_heat = df_heat.pivot(index='dia_semana',
                            columns='hora',
                            values='cluster').fillna(0)
    df_heat = df_heat.reindex(DIAS).reset_index()
    df_heat = pd.melt(df_heat, id_vars='dia_semana')
    df_heat = df_heat.assign(value=df_heat['value'].astype(int))
    heatmap_opts = dict(width=600, height=300,
                        cmap='viridis',
                        colorbar=True,
                        show_title=True, tools=['hover'])
    heatmap = hv.HeatMap(
        df_heat, kdims=['hora', 'dia_semana'], vdims=['value'],
        label=f'Incidentes por día y hora en el cluster: {indice}'
    ).options(**heatmap_opts)
    return heatmap


# el index es una lista, se tiene que agarrar sólo uno
def tap_to_heatmap(index):
    if index:
        cluster = index_to_cluster[index[0]]
        return generar_heatmap(cluster, index[0])
    else:
        return empty_heatmap()


points_opts = dict(alpha=0.35, color='firebrick')
points = gv.Points(df_points_in_clusters,
                   kdims=['longitud', 'latitud'],
                   vdims=['cluster']).options(**points_opts)

centros_opts = dict(
    cmap='viridis',
    size_index=2,
    color_index=2,
    alpha=0.65,
    logz=True,
    colorbar=True,
    tools=['hover', 'tap'],
    scaling_factor=1.5
)

centros_elemets = {
    i: hv.Points({'x': row.x, 'y': row.y, 'cluster_size': row.cluster_size},
                  kdims=['x', 'y'],
                  vdims=['cluster_size']).options(**centros_opts)
    for i, row in enumerate(df_centros.itertuples())
}

nd_centros = hv.NdOverlay(centros_elemets)
selection_centros = hv.streams.Selection1D(source=nd_centros)
dmap = hv.DynamicMap(tap_to_heatmap, streams=[selection_centros])

tiles_opts = dict(width=width, height=height, bgcolor='black',
                  xaxis=None, yaxis=None,
                  show_grid=False, toolbar='above')
tiles = gv.tile_sources.Wikipedia.clone().options(**tiles_opts)

mapa = tiles * nd_centros * points
layout = dmap + mapa

renderer = hv.renderer('bokeh')
doc = renderer.server_doc(layout)
doc.title = 'Clusters de accidentes'
