import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import io

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Procesador de Datos Excel",
    page_icon="📁",
    layout="wide"
)

# --- Funciones de Limpieza y Validación ---
def clean_phone(phone):
    """Limpia y valida un número de teléfono colombiano."""
    if phone is None or pd.isna(phone):
        return None
    # Elimina todo lo que no sea un dígito
    cleaned = re.sub(r'\D', '', str(phone))
    # Valida la longitud y el prefijo para números móviles/fijos comunes
    if not cleaned or cleaned.lower() == 'nan' or len(cleaned) != 10:
        return None
    # Los números móviles en Colombia empiezan por 3. Los fijos por 60 + indicativo.
    # Esta validación asume números móviles de 10 dígitos.
    if cleaned[0] != '3': # Simplificamos asumiendo que la mayoría son móviles de 10 dígitos
        # Podríamos añadir una lógica más compleja para fijos si fuera necesario
        pass
    return cleaned

def validate_email(email):
    """Valida si un string tiene formato de email."""
    if email is None or pd.isna(email):
        return None
    email_str = str(email).strip().lower()
    # Expresión regular para validar emails
    email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    return email_str if email_regex.match(email_str) else None

# --- Interfaz de la Aplicación ---
st.title("✨ Procesador de Teléfonos y Correos Colombianos ✨")
st.markdown("Carga tus archivos Excel, selecciona las columnas y obtén tus datos limpios y listos para usar.")

# Zona de carga de archivos
st.header("1. Cargar Archivos Excel")
uploaded_files = st.file_uploader(
    "Arrastra y suelta todos tus archivos Excel aquí (.xlsx, .xls)",
    type=['xlsx', 'xls'],
    accept_multiple_files=True
)

if uploaded_files:
    df_list = []
    total_rows_initial = 0
    for file in uploaded_files:
        try:
            st.write(f"📄 Procesando archivo: `{file.name}`")
            df_temp = pd.read_excel(file, engine='openpyxl')
            total_rows_initial += len(df_temp)
            df_temp['_sourceFile'] = file.name # Añadir columna para saber el origen
            df_list.append(df_temp)
        except Exception as e:
            st.error(f"Error al leer el archivo {file.name}: {e}")
    
    if df_list:
        df = pd.concat(df_list, ignore_index=True)
        st.success(f"✅ ¡Carga completa! Se han procesado {len(uploaded_files)} archivos con un total de {len(df)} filas.")
        
        st.header("2. Configurar Columnas")
        
        available_cols = [c for c in df.columns if c != '_sourceFile']
        
        # Crear columnas para los selectores
        col1, col2 = st.columns(2)
        
        with col1:
            phone_col = st.selectbox("Selecciona la columna de Teléfonos:", options=["-- No procesar --"] + available_cols, key="phone_select")
        with col2:
            email_col = st.selectbox("Selecciona la columna de Emails:", options=["-- No procesar --"] + available_cols, key="email_select")

        if st.button("🚀 Procesar Datos", type="primary"):
            with st.spinner('Realizando la magia... por favor espera.'):
                
                # --- Lógica de Procesamiento ---
                df_processed = df.copy() # Trabajar sobre una copia
                
                if phone_col != "-- No procesar --":
                    df_processed['cleanPhone'] = df_processed[phone_col].apply(clean_phone)
                if email_col != "-- No procesar --":
                    df_processed['validEmail'] = df_processed[email_col].apply(validate_email)

                st.header("3. Resultados y Descarga")
                
                # --- Reporte de Calidad ---
                stats = {'Métrica': [], 'Valor': []}
                stats['Métrica'].append('Total de filas analizadas')
                stats['Valor'].append(len(df_processed))

                if phone_col != "-- No procesar --":
                    valid_phones = df_processed['cleanPhone'].count()
                    unique_phones = df_processed['cleanPhone'].nunique()
                    stats['Métrica'].extend(['Teléfonos válidos encontrados', 'Teléfonos únicos'])
                    stats['Valor'].extend([valid_phones, unique_phones])

                if email_col != "-- No procesar --":
                    valid_emails = df_processed['validEmail'].count()
                    unique_emails = df_processed['validEmail'].nunique()
                    stats['Métrica'].extend(['Emails válidos encontrados', 'Emails únicos'])
                    stats['Valor'].extend([valid_emails, unique_emails])

                stats_df = pd.DataFrame(stats)
                
                st.subheader("📊 Reporte de Calidad de Datos")
                st.dataframe(stats_df, use_container_width=True)
                
                # --- Preparar archivos para descarga ---
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Hoja con datos completos procesados
                    df_final_display = df_processed.rename(columns={'cleanPhone': 'Telefono_Limpio', 'validEmail': 'Email_Limpio'})
                    df_final_display.to_excel(writer, sheet_name="Datos_Completos_Procesados", index=False)
                    
                    # Hojas con valores únicos
                    if phone_col != "-- No procesar --":
                        pd.DataFrame(df_processed['cleanPhone'].dropna().unique(), columns=['Telefono']).to_excel(writer, sheet_name="Telefonos_Unicos", index=False)
                    if email_col != "-- No procesar --":
                        pd.DataFrame(df_processed['validEmail'].dropna().unique(), columns=['Email']).to_excel(writer, sheet_name="Emails_Unicos", index=False)
                
                processed_data = output.getvalue()

                st.subheader("⬇️ Descargar Archivo de Resultados")
                st.download_button(
                    label="Descargar Todo en un Excel",
                    data=processed_data,
                    file_name=f"datos_procesados_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.balloons()

