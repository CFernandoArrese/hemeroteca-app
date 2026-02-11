import streamlit as st
import pandas as pd
import unicodedata
import datetime
import os
import glob

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Hemeroteca Lambayeque", page_icon="📰", layout="wide")

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
    # Busca archivos Excel sueltos (ignora los temporales ~$)
    todos_xlsx = glob.glob("*.xlsx") + glob.glob("*.xls")
    archivos = [f for f in todos_xlsx if not os.path.basename(f).startswith('~$')]
    
    lista_dfs = []
    
    if not archivos:
        return pd.DataFrame(), 0

    # Barra de carga invisible (para que sea rápido)
    for i, ruta in enumerate(archivos):
        try:
            # header=1 (fila 2 es titulo). Si falla, intenta header=0
            try:
                df_temp = pd.read_excel(ruta, header=1)
            except:
                df_temp = pd.read_excel(ruta, header=0)
                
            lista_dfs.append(df_temp)
        except:
            pass
            
    if lista_dfs:
        return pd.concat(lista_dfs, ignore_index=True), len(archivos)
    return pd.DataFrame(), 0

# --- INTERFAZ ---

# 1. TU TÍTULO PERSONALIZADO
st.title('HEMEROTECA "LAMBAYEQUE" de Miandito (Miguel Angel Diaz Torres)')
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
        df['Ubicación'] = "Ver Excel"

    # Indice de búsqueda
    cols_texto = [c for c in df.columns if c != 'Busqueda_Index']
    df['Busqueda_Index'] = df[cols_texto].fillna('').astype(str).agg(' '.join, axis=1).apply(normalizar_texto)

    # Mensaje de estado
    st.success(f"✅ Sistema activo: {cantidad} libros cargados ({len(df)} recortes).")

    # Buscador
    busqueda = st.text_input("🔍 Buscar:", placeholder="Escribe título, tema o año...")
    
    # 2. SELECCIÓN DE COLUMNAS (YA NO ESTÁ 'ORIGEN')
    cols_mostrar = ['Titulo', 'Autor', 'Fecha_Legible', 'Periodico', 'Observaciones', 'Ubicación']
    cols_finales = [c for c in cols_mostrar if c in df.columns]

    if busqueda:
        res = df[df['Busqueda_Index'].str.contains(normalizar_texto(busqueda))]
        if not res.empty:
            st.info(f"Encontrados: {len(res)}")
            st.dataframe(res[cols_finales], use_container_width=True, hide_index=True)
        else:
            st.warning("No hay resultados.")
    else:
        # Muestra los primeros 10
        st.dataframe(df.head(10)[cols_finales], use_container_width=True, hide_index=True)

else:
    st.error("⚠️ No encontré los archivos Excel.")
    st.info("Asegúrate de que los archivos .xlsx estén en la misma carpeta que este código.")
