import streamlit as st
import pandas as pd
import unicodedata
import datetime
import os
import glob

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Hemeroteca Master", page_icon="🏛️", layout="wide")

# --- FUNCIONES ---
def normalizar_texto(texto):
    if pd.isna(texto) or texto == "": return ""
    texto = str(texto)
    texto = unicodedata.normalize('NFD', texto)
    return texto.encode('ascii', 'ignore').decode('utf-8').lower()

def formatear_fecha(valor):
    if pd.isna(valor): return ""
    if isinstance(valor, (int, float)):
        return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=valor)).strftime('%d/%m/%Y')
    return str(valor)

@st.cache_data
def cargar_biblioteca():
    # CAMBIO IMPORTANTE: Busca archivos Excel AQUÍ MISMO (en la raíz), no en carpetas
    # Excluimos archivos temporales de Excel (los que empiezan con ~$)
    todos_xlsx = glob.glob("*.xlsx") + glob.glob("*.xls")
    archivos = [f for f in todos_xlsx if not os.path.basename(f).startswith('~$')]
    
    lista_dfs = []
    
    # Barra de progreso
    if not archivos:
        return pd.DataFrame(), 0

    barra = st.progress(0)
    
    for i, ruta in enumerate(archivos):
        try:
            # Header 1 porque tu archivo tiene título en la fila 1
            df_temp = pd.read_excel(ruta, header=1)
            df_temp['Origen'] = os.path.basename(ruta)
            lista_dfs.append(df_temp)
        except Exception:
            # Si falla, intentamos sin saltar filas (header=0) por si acaso
            try:
                df_temp = pd.read_excel(ruta, header=0)
                df_temp['Origen'] = os.path.basename(ruta)
                lista_dfs.append(df_temp)
            except:
                pass
        
        barra.progress((i + 1) / len(archivos))
    
    barra.empty()
    
    if lista_dfs:
        return pd.concat(lista_dfs, ignore_index=True), len(archivos)
    return pd.DataFrame(), 0

# --- INTERFAZ ---
st.title("🏛️ Buscador Hemeroteca Global")
st.markdown("---")

df, cantidad = cargar_biblioteca()

if not df.empty:
    # Procesamiento
    col_tomo = next((c for c in df.columns if 'tomo' in str(c).lower()), None)
    col_pag = next((c for c in df.columns if 'pag' in str(c).lower()), None)
    col_fecha = next((c for c in df.columns if 'fecha' in str(c).lower()), 'Fecha')
    
    if col_fecha in df.columns:
        df['Fecha_Legible'] = df[col_fecha].apply(formatear_fecha)
    else:
        df['Fecha_Legible'] = ""

    if col_tomo and col_pag:
        df['Ubicación'] = df.apply(lambda r: f"📘 T.{r[col_tomo]} | 📄 P.{r[col_pag]}", axis=1)
    else:
        df['Ubicación'] = "Ver Excel Original"

    cols_texto = [c for c in df.columns if c not in ['Busqueda_Index']]
    df['Busqueda_Index'] = df[cols_texto].fillna('').astype(str).agg(' '.join, axis=1).apply(normalizar_texto)

    # Buscador
    st.success(f"✅ Buscando en **{cantidad} libros** ({len(df)} recortes).")
    busqueda = st.text_input("🔍 ¿Qué buscas?", placeholder="Escribe aquí...")
    
    cols_mostrar = ['Titulo', 'Autor', 'Fecha_Legible', 'Periodico', 'Observaciones', 'Ubicación', 'Origen']
    cols_finales = [c for c in cols_mostrar if c in df.columns]

    if busqueda:
        res = df[df['Busqueda_Index'].str.contains(normalizar_texto(busqueda))]
        if not res.empty:
            st.info(f"Encontrados: {len(res)}")
            st.dataframe(res[cols_finales], use_container_width=True, hide_index=True)
        else:
            st.warning("Sin resultados.")
    else:
        st.dataframe(df.head(10)[cols_finales], use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ No encontré archivos Excel junto a este programa.")