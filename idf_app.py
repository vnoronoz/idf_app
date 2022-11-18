# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 13:54:37 2022

@author: D732506
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.io as pio
import warnings

pio.templates.default = "plotly_white"
pd.options.mode.chained_assignment = None
warnings.simplefilter(action='ignore', category=UserWarning) 

st.set_page_config(page_title='IDF Viewer')
st.header('Visor de intensidad de pluviometría')
#st.subheader('Visor Curvas IDF')


def get_key_from_value(d, val):
    return [k for k, v in d.items() if v == val]


# --- ARRANGE RELATIVE PATHS

dirname = os.path.dirname(__file__)

codes_dirname = os.path.join(dirname,'codes')
idf_dirname = os.path.join(dirname,'idf_excel')
data_dirname = os.path.join(dirname,'data')

#codes_file = os.path.join(codes_dirname,'SAD_Cuencas.xlsx')
codes_file = os.path.join(codes_dirname,'SAD_Cuencas_Planes.xlsx')
data_file = os.path.join(data_dirname,'Resumen_historico.xlsx')

# --- LOAD DATA

# Archivo codigos cuencas SAD
df_codes = pd.read_excel(codes_file, header = 0, engine='openpyxl')
dict_codes = dict(zip(df_codes.COD_SAD, df_codes.CUENCA))

# Archivo recopilacion episodios historicos
df_data_pluvio = pd.read_excel(data_file, header = 0, sheet_name = 'Pluviometros', engine='openpyxl')
df_data_pluvio['Fecha'] = pd.to_datetime(df_data_pluvio['Fecha'], format='%Y-%m-%d').dt.date

df_data_cuenca = pd.read_excel(data_file, header = 0, sheet_name = 'Cuencas', engine='openpyxl')
df_data_cuenca['Fecha'] = pd.to_datetime(df_data_cuenca['Fecha'], format='%Y-%m-%d').dt.date


# --- LISTADOS OPCIONES A ELEGIR
# Cuenca
basin_list = sorted(df_codes['CUENCA'].unique())

# Modo analisis pluviometro/cuenca
analysis_mode = ['Cuenca (Precipitación interpolada en cuenca)', 'Pluviómetro (Precipitación medida en pluviómetro)']


# --- STREAMLIT BASIN SELECTION
basin_selection = st.selectbox(label='¿Qué cuenca quieres analizar?', options=basin_list)


# Data for the selected basin
basin_key = get_key_from_value(dict_codes, basin_selection)
basin = basin_key[0]

existing_basins = os.listdir(idf_dirname)
matching_file = [s for s in existing_basins if basin in s]

# Select IDF file from directory for the selected basin
idf_file = os.path.join(idf_dirname, matching_file[0])
df_idf_values = pd.read_excel(idf_file, header = 0, index_col=0)
df_idf_values.rename_axis(None, axis=1, inplace=True)
# Delete row with index label 72 
df_idf_values_48h = df_idf_values.drop(72)

# Select pluvio and basin historical data for the selected basin
df_basin_pluvio = df_data_pluvio.loc[df_data_pluvio['Codigo_Cuenca'] == basin]
df_basin_cuenca = df_data_cuenca.loc[df_data_cuenca['Codigo_Cuenca'] == basin]

# Dates and pluvios for the selected basin
basin_dates = sorted(df_basin_cuenca['Fecha'].unique())
pluvio_dates = sorted(df_basin_pluvio['Fecha'].unique())
available_pluvios = sorted(df_basin_pluvio['Pluviómetro'].unique())

# Colores TR IDF curves
color_dict= {'t2': 'cyan',
             't5': 'blue',
             't10': 'green',
             't25': 'gold',
             't50': 'orange',
             't100': 'red',
             't500': 'indigo'}

# --- STREAMLIT RADIO BUTTON

if pluvio_dates or basin_dates:
    
    mode_selection = st.radio(label='¿Qué datos quieres ver?', options=analysis_mode)
    st.write('Has seleccionado analizar datos de', mode_selection)


# --- STREAMLIT EPISODE SELECTION

    if str(mode_selection) == 'Cuenca (Precipitación interpolada en cuenca)':  #datos de cuencas
        
        # holding the spot for the graph
        plot_spot = st.empty() 
        
        st.write('Estás viendo las curvas IDF de la cuenca:', basin_selection)
        
        container = st.container()
        all_episodes = st.checkbox('Seleccionar todos los episodios')
 
        if all_episodes:
            
            episode_selection = container.multiselect('¿Qué episodios quieres ver?', options=basin_dates, default=basin_dates)
        
        else:
            
            episode_selection =  container.multiselect('¿Qué episodios quieres ver?', options=basin_dates)
        
        
        
        mask = df_basin_cuenca['Fecha'].isin(episode_selection)        
        episodes_basin_df = df_basin_cuenca[mask]        
        
        # Show dataframe
        st.dataframe(episodes_basin_df[['Fecha','SPEI (CSIC)', 'Indice Sequía (PES)','Reserva nival (ERHIN)']])
        
        df_idf_basin_cuenca =  episodes_basin_df[['Fecha',
                                                  'PP max. 10 min (mm)',
                                                  'PP max. 30 min (mm)',
                                                  'PP max. 1 h (mm)',
                                                  'PP max. 3 h (mm)',
                                                  'PP max. 4 h (mm)',
                                                  'PP max. 6 h (mm)',
                                                  'PP max. 12 h (mm)',
                                                  'PP max. 24 h (mm)',
                                                  'PP max. 48 h (mm)']]
        
        df_idf_basin_cuenca['Fecha'] = df_idf_basin_cuenca['Fecha'].astype(str)
        df_idf_basin_graph = df_idf_basin_cuenca.T
        df_idf_basin_graph.columns = df_idf_basin_graph.iloc[0]
        df_idf_basin_graph.rename(index={'PP max. 10 min (mm)': 0.167,
                    'PP max. 30 min (mm)': 0.5,
                     'PP max. 1 h (mm)': 1,
                     'PP max. 3 h (mm)': 3,
                     'PP max. 4 h (mm)': 4,
                     'PP max. 6 h (mm)': 6, 
                     'PP max. 12 h (mm)': 12,
                     'PP max. 24 h (mm)': 24, 
                     'PP max. 48 h (mm)': 48}, inplace=True)
        
        df_idf_basin_graph.drop('Fecha', inplace=True)
        df_idf_basin_graph.rename_axis(None, axis=1, inplace=True)


        # Dataframe from wide to a long format
        df_idf_basin_graph['Duracion (h)'] = df_idf_basin_graph.index
        df_idf_basin_graph = pd.melt(df_idf_basin_graph, id_vars='Duracion (h)',
                                     value_vars=df_idf_basin_graph.columns[:-1],
                                     var_name='Evento', value_name='Intensidad PP (mm)')
        
        df_idf_values_48h['Duracion (h)'] = df_idf_values_48h.index
        df_idf_values_48h = pd.melt(df_idf_values_48h, id_vars='Duracion (h)',
                                     value_vars=df_idf_values_48h.columns[:-1],
                                     var_name='Evento', value_name='Intensidad PP (mm)')

        frames = [df_idf_basin_graph, df_idf_values_48h]
        result = pd.concat(frames)
        
        
        # Now code the plotly chart based on the widget selection        
        fig = px.line(result, color_discrete_map=color_dict, x='Duracion (h)', y='Intensidad PP (mm)', color='Evento')
        # Asignar colores a los TR
        fig.for_each_trace(
            lambda trace: trace.update(line=dict(dash='dash', width=1.5)) if trace.name.startswith('t') else (),
            )
        #fig.update_layout(xaxis = dict(range=[0, 48], tickmode = 'linear', dtick = 2))
        #fig.update_layout(yaxis = dict(tickmode = 'linear', dtick = 25))
        fig.update_layout(plot_bgcolor = "white")        
        
    
    else: # datos pluviometros
                
        
        plot_spot = st.empty() # holding the spot for the graph
        
        st.write('Estás viendo las curvas IDF de la cuenca:', basin_selection)
        
        container2 = st.container()
        all_pluvios = st.checkbox('Seleccionar todos los pluviómetros')
 
        if all_pluvios:
            
            pluvio_selection = container2.multiselect('¿Qué pluviómetros quieres ver?', options=available_pluvios, default=available_pluvios)
        
        else:
            
            pluvio_selection =  container2.multiselect('¿Qué pluviómetros quieres ver?', options=available_pluvios)
        
        container1 = st.container()
        all_episodes = st.checkbox('Seleccionar todos los episodios')
 
        if all_episodes:
            
            episode_selection = container1.multiselect('¿Qué episodios quieres ver?', options=pluvio_dates, default=pluvio_dates)
        
        else:
            
            episode_selection =  container1.multiselect('¿Qué episodios quieres ver?', options=pluvio_dates)
            
        
        
        mask = df_basin_pluvio['Fecha'].isin(episode_selection) & df_basin_pluvio['Pluviómetro'].isin(pluvio_selection)
        episodes_pluvio_df = df_basin_pluvio[mask]
        
        st.dataframe(episodes_pluvio_df[['Pluviómetro', 'Fecha','SPEI (CSIC)', 'Indice Sequía (PES)','Reserva nival (ERHIN)']])
        
        df_idf_basin_pluvio =  episodes_pluvio_df[['Fecha', 'Pluviómetro',
                                                  'PP max. 10 min (mm)',
                                                  'PP max. 30 min (mm)',
                                                  'PP max. 1 h (mm)',
                                                  'PP max. 3 h (mm)',
                                                  'PP max. 4 h (mm)',
                                                  'PP max. 6 h (mm)',
                                                  'PP max. 12 h (mm)',
                                                  'PP max. 24 h (mm)',
                                                  'PP max. 48 h (mm)']]
             
        df_idf_basin_pluvio['Fecha'] = df_idf_basin_pluvio['Fecha'].astype(str)
        
        df_idf_basin_pluvio['ident'] = df_idf_basin_pluvio[['Fecha', 'Pluviómetro']].agg('-'.join, axis=1)
        df_idf_basin_pluvio.drop(['Fecha', 'Pluviómetro'], axis=1, inplace=True)
        df_idf_basin_pluvio.rename({'ident': 'Fecha'}, axis=1, inplace=True)
        
        df_idf_pluvio_graph = df_idf_basin_pluvio.T
        df_idf_pluvio_graph.columns = df_idf_pluvio_graph.iloc[9]
        df_idf_pluvio_graph.rename(index={'PP max. 10 min (mm)': 0.167,
                    'PP max. 30 min (mm)': 0.5,
                     'PP max. 1 h (mm)': 1,
                     'PP max. 3 h (mm)': 3,
                     'PP max. 4 h (mm)': 4,
                     'PP max. 6 h (mm)': 6, 
                     'PP max. 12 h (mm)': 12,
                     'PP max. 24 h (mm)': 24, 
                     'PP max. 48 h (mm)': 48}, inplace=True)
        
        df_idf_pluvio_graph.drop('Fecha', inplace=True)
        df_idf_pluvio_graph.rename_axis(None, axis=1, inplace=True)
        
        df_idf_pluvio_graph['Duracion (h)'] = df_idf_pluvio_graph.index
        df_idf_pluvio_graph = pd.melt(df_idf_pluvio_graph, id_vars=['Duracion (h)'], 
                                     value_vars=df_idf_pluvio_graph.columns[:-1],
                                     var_name='Evento', value_name='Intensidad PP (mm)')
        
        df_idf_values_48h['Duracion (h)'] = df_idf_values_48h.index
        df_idf_values_48h = pd.melt(df_idf_values_48h, id_vars='Duracion (h)',
                                     value_vars=df_idf_values_48h.columns[:-1],
                                     var_name='Evento', value_name='Intensidad PP (mm)')

        frames = [df_idf_pluvio_graph, df_idf_values_48h]
        result = pd.concat(frames)
        
        fig = px.line(result, color_discrete_map=color_dict, x='Duracion (h)', y='Intensidad PP (mm)', color='Evento')
        fig.for_each_trace(
            lambda trace: trace.update(line=dict(dash='dash', width=1.5)) if trace.name.startswith('t') else (),
            )
        #fig.update_layout(xaxis = dict(range=[0, 48], tickmode = 'linear', dtick = 2))
        #fig.update_layout(yaxis = dict(tickmode = 'linear', dtick = 25))
        fig.update_layout(plot_bgcolor = "white")
    

    st.write('AÑADIR DATOS:')
        
    uploaded_file = st.file_uploader('Elige un archivo')
    
    if uploaded_file is not None:    
                   
            #try:
                df_new_data = pd.read_excel(uploaded_file, header = 0, index_col = 0)
                print(df_new_data)
                df_new_data.rename(index={'PP max. 10 min (mm)': 0.167,
                            'PP max. 30 min (mm)': 0.5,
                             'PP max. 1 h (mm)': 1,
                             'PP max. 3 h (mm)': 3,
                             'PP max. 4 h (mm)': 4,
                             'PP max. 6 h (mm)': 6, 
                             'PP max. 12 h (mm)': 12,
                             'PP max. 24 h (mm)': 24,
                             'PP max. 48 h (mm)': 48}, inplace=True)
                df_new_data['Duracion (h)']=df_new_data.index
                df_new_data = pd.melt(df_new_data, id_vars='Duracion (h)', value_vars=df_new_data.columns[:-1], var_name='Evento', value_name='Intensidad PP (mm)')
                print(df_new_data)
                # Borrar la columna Unnamed si existe
                df_new_data = df_new_data.loc[:, ~df_new_data.columns.str.startswith('Unnamed')]
                print(df_new_data)
                df_new_data['Evento'] = pd.to_datetime(df_new_data['Evento'], format='%Y-%m-%d').dt.date
                df_new_data['Evento'] = df_new_data['Evento'].astype(str)
                print(df_new_data)

                fig.add_traces(
                    list(px.line(df_new_data, x='Duracion (h)', y='Intensidad PP (mm)', color='Evento').select_traces())
                    )
            #except:
                #pass
        
    # --- STREAMLIT CHART
    
    #send the plotly chart to it's spot "in the line" 
    with plot_spot:
        st.plotly_chart(fig, use_container_width=True)
