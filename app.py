import streamlit as st
import pandas as pd
import re
import io

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Extractor y Limpiador de Datos",
    page_icon="🔎",
    layout="wide"
)

# --- Funciones de Extracción y Limpieza ---

def extract_and_clean_data(df, columns_to_search):
    """
    Busca en las columnas seleccionadas de un DataFrame para extraer y limpiar
    números de teléfono y correos electrónicos.
    """
    all_phones = []
    all_emails = []

    # Regex para encontrar emails y teléfonos colombianos de 10 dígitos.
    email_regex = re.compile(r'[\w\.\-]+@[\w\.\-]+')
    phone_regex = re.compile(r'(?<!\d)\d{10}(?!\d)') # Encuentra exactamente 10 dígitos

    for index, row in df.iterrows():
        found_phones = set()
        found_emails = set()

        # Itera sobre las columnas que el usuario seleccionó
        for col in columns_to_search:
            cell_value = str(row[col])

            # Extraer emails
            emails_in_cell = email_regex.findall(cell_value)
            for email in emails_in_cell:
                # Simple validación final
                if '.' in email.split('@')[-1]:
                    found_emails.add(email.lower())

            # Extraer teléfonos
            phones_in_cell = phone_regex.findall(cell_value)
            for phone in phones_in_cell:
                 # Validación de prefijo colombiano
                if phone.startswith('3'):
                    found_phones.add(phone)

        all_phones.append(list(found_phones))
        all_emails.append(list(found_emails))

    # Crear un nuevo DataFrame con los resultados
    # Se toma el primer teléfono/email encontrado por fila para simplicidad en la salida
    # Se podría expandir para manejar múltiples contactos por fila si es necesario
    results_df = pd.DataFrame({
        'Telefono': [p[0] if p else None for p in all_phones],
        'Correo': [e[0] if e else None for e in all_emails]
    })
    
    # Eliminar filas donde no se encontró ni teléfono ni correo
    results_df.dropna(how='all', inplace=True)
    # Eliminar duplicados exactos
    results_df.drop_duplicates(inplace=True)
    
    return results_df


# --- Interfaz de la Aplicación ---
st.title("🔎 Extractor y Limpiador Inteligente")
st.markdown("Sube un archivo Excel con datos desordenados y la herramienta extraerá los teléfonos y correos válidos.")

# 1. Carga de Archivos
st.header("1. Cargar Archivo Excel")
uploaded_file = st.file_uploader(
    "Arrastra y suelta tu archivo Excel aquí (.xlsx, .xls)",
    type=['xlsx', 'xls']
)

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    st.success(f"✅ Archivo `{uploaded_file.name}` cargado. Contiene {len(df)} filas.")
    st.write("Vista previa de los datos originales:")
    st.dataframe(df.head())

    # 2. Selección de Columnas para Analizar
    st.header("2. Seleccionar Columnas a Analizar")
    st.info("Elige todas las columnas que podrían contener teléfonos o correos, incluso si están mezclados.")
    
    options = df.columns.tolist()
    columns_to_search = st.multiselect(
        "Columnas para buscar:",
        options=options,
        default=options  # Por defecto, selecciona todas
    )

    # 3. Procesamiento y Descarga
    if st.button("🚀 Extraer y Procesar Datos", type="primary"):
        if not columns_to_search:
            st.warning("Por favor, selecciona al menos una columna para analizar.")
        else:
            with st.spinner('Analizando y extrayendo datos...'):
                clean_df = extract_and_clean_data(df, columns_to_search)
            
            st.header("3. Resultados Extraídos y Limpios")
            st.success(f"¡Proceso completado! Se encontraron {len(clean_df)} contactos únicos y válidos.")
            st.dataframe(clean_df)

            # Preparar archivo para descarga
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                clean_df.to_excel(writer, index=False, sheet_name='Contactos Limpios')
            
            processed_data = output.getvalue()

            st.download_button(
                label="⬇️ Descargar Excel Limpio",
                data=processed_data,
                file_name=f"contactos_limpios_{uploaded_file.name}",
                mime="application/vnd.ms-excel"
            )
