import streamlit as st
import pandas as pd
import re
import io

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Extractor Inteligente de Contactos",
    page_icon="🎯",
    layout="wide"
)

# --- Funciones de Extracción y Limpieza (sin cambios) ---
def extract_and_clean_data(df, columns_to_search):
    """
    Busca en las columnas seleccionadas para extraer teléfonos y correos.
    """
    all_rows_data = []

    email_regex = re.compile(r'[\w\.\-]+@[\w\.\-]+')
    phone_regex = re.compile(r'\b(3\d{9})\b')

    for index, row in df.iterrows():
        found_phones = set()
        found_emails = set()

        for col in columns_to_search:
            cell_value = str(row[col])

            emails_in_cell = email_regex.findall(cell_value)
            for email in emails_in_cell:
                if '.' in email.split('@')[-1]:
                    found_emails.add(email.lower())

            phones_in_cell = phone_regex.findall(cell_value)
            found_phones.update(phones_in_cell)

        all_rows_data.append({
            "Telefonos": list(found_phones),
            "Correos": list(found_emails)
        })

    final_df = pd.DataFrame({
        'Telefono': [p["Telefonos"][0] if p["Telefonos"] else None for p in all_rows_data],
        'Correo': [e["Correos"][0] if e["Correos"] else None for e in all_rows_data]
    })
    
    final_df.dropna(how='all', inplace=True)
    final_df.drop_duplicates(inplace=True)
    
    return final_df

# --- Interfaz de la Aplicación ---
st.title("🎯 Extractor Inteligente de Contactos")
st.markdown("Sube tus archivos Excel y la herramienta encontrará y limpiará los contactos automáticamente.")

# 1. Carga de Múltiples Archivos
st.header("1. Cargar Archivos Excel")
uploaded_files = st.file_uploader(
    "Arrastra y suelta todos tus archivos Excel aquí",
    type=['xlsx', 'xls'],
    accept_multiple_files=True
)

if uploaded_files:
    df_list = []
    for file in uploaded_files:
        df_temp = pd.read_excel(file, engine='openpyxl')
        df_list.append(df_temp)
    
    df = pd.concat(df_list, ignore_index=True)
    st.success(f"✅ ¡Carga completa! Se han unido {len(uploaded_files)} archivos, sumando un total de {len(df)} filas.")
    
    # 2. Selección de Columnas (CON LA MEJORA)
    st.header("2. Configurar Búsqueda")
    
    all_column_options = df.columns.tolist()
    
    # --- LÓGICA DE DETECCIÓN AUTOMÁTICA ---
    keywords = ['tel', 'phone', 'telefono', 'móvil', 'celular', 'cel', 'email', 'correo', 'mail', '@']
    default_selections = [col for col in all_column_options if any(keyword in str(col).lower() for keyword in keywords)]
    # --- FIN DE LA LÓGICA ---
    
    st.info("La herramienta ha preseleccionado las columnas que parecen contener contactos. Puedes añadir o quitar columnas manualmente.")
    
    columns_to_search = st.multiselect(
        "Columnas donde buscar:",
        options=all_column_options,
        default=default_selections  # <-- ¡AQUÍ ESTÁ LA MAGIA!
    )

    # 3. Procesamiento y Descarga
    if st.button("🚀 Extraer y Procesar Datos", type="primary"):
        if not columns_to_search:
            st.warning("Por favor, selecciona al menos una columna para analizar.")
        else:
            with st.spinner('Buscando y limpiando contactos en las columnas seleccionadas...'):
                clean_df = extract_and_clean_data(df, columns_to_search)
            
            st.header("3. Resultados Finales")
            st.success(f"¡Proceso completado! Se encontraron {len(clean_df)} contactos únicos y válidos.")
            st.dataframe(clean_df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                clean_df.to_excel(writer, index=False, sheet_name='Contactos Limpios')
            
            processed_data = output.getvalue()

            st.download_button(
                label="⬇️ Descargar Excel Limpio",
                data=processed_data,
                file_name="contactos_extraidos_limpios.xlsx",
                mime="application/vnd.ms-excel"
            )
