import ujson
import pyproj
import pandas as pd


def load_axa_data(path) -> pd.DataFrame:
    """Carga archivo geojson de axa como un dataframe y
    hace un preprocesamiento"""
    with open(path, 'r') as file:
        data = ujson.load(file)
    data_features = data['features']
    df_info = pd.DataFrame([row['properties'] for row in data_features])
    df_info = df_info.drop(['punto_geografico', 'the_geom_c_254', 'the_geom_w_c_254'], 
                           axis=1)
    meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
             'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    meses_to_number = {m: f'{i}'.zfill(2) for i, m in enumerate(meses, start=1)}
    df_info.loc[:, 'hora_n_10_0'] = df_info.hora_n_10_0.astype(str).str.pad(2, fillchar='0')
    df_info.loc[:, 'dia_numero_n_10_0'] = df_info.dia_numero_n_10_0.astype(str).str.pad(2, fillchar='0')
    df_info.loc[:, 'mes_c_254'] = df_info.mes_c_254.replace(meses_to_number)
    fecha = df_info.ano_n_10_0 + '-' + df_info.mes_c_254 + '-' + df_info.dia_numero_n_10_0
    df_info = df_info.assign(fecha=pd.to_datetime(fecha, format='%Y-%m-%d'),
                             latitud_n_24_15=df_info.latitud_n_24_15.astype(float),
                             longitud_n_24_15=df_info.longitud_n_24_15.astype(float))
    df_info = df_info.rename(columns={'latitud_n_24_15': 'latitud', 
                                      'longitud_n_24_15': 'longitud', 
                                      'dia_c_254': 'dia_semana', 
                                      'hora_n_10_0': 'hora'})
    df_info = df_info
    return df_info


def wgs84_to_mercator(lat, lon):
    x, y = pyproj.transform(
        pyproj.Proj(init='epsg:4326'), 
        pyproj.Proj(init='epsg:3857'),
        lon, lat
    )
    return y, x