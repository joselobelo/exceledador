import streamlit as st
import pandas as pd
import re
import io

# --- Configuración de la Página de la Aplicación ---
st.set_page_config(
    page_title="Generador de Bases con Reporte de Errores",
    page_icon="📊",
    layout="wide"
)

# --- Función Principal de Extracción y Formateo (CON MANEJO DE ERRORES) ---
def extract_and_format_with_error_handling(df, phone_cols, name_cols):
    """
    Extrae contactos válidos y, al mismo tiempo, captura y reporta los inválidos.
    Devuelve dos DataFrames: uno con datos válidos y otro con los errores.
    """
    valid_records = []
    error_records = []
    
    # Regex: Uno para encontrar teléfonos VÁLIDOS y otro para encontrar CUALQUIER secuencia de 7+ dígitos.
    valid_phone_regex = re.compile(r'\b(3\d{9})\b')
    potential_phone_regex = re.compile(r'\d{7,}') # Captura secuencias de 7 o más dígitos

    for index, row in df.iterrows():
        # Extraer el nombre de la fila primero para usarlo en ambos reportes (válido y error)
        found_name = "Contacto Desconocido"
        for col in name_cols:
            name_raw = str(row.get(col, ''))
            name_clean = re.sub(r'[^a-zA-Z\s]', '', name_raw).strip()
            words = name_clean.split()
            for word in words:
                if len(word) > 2:
                    found_name = word.capitalize()
                    break
            if found_name != "Contacto Desconocido":
                break

        # Buscar teléfonos en la fila
        phone_found_in_row = False
        row_errors = set() # Usar un set para no reportar el mismo error varias veces por fila

        for col in phone_cols:
            cell_value = str(row.get(col, ''))
            
            # 1. Intentar encontrar un teléfono perfectamente válido
            valid_phones = valid_phone_regex.findall(cell_value)
            if valid_phones:
                valid_records.append({
                    "Numero telefono": valid_phones[0], "value1": found_name, "value2": "", 
                    "value3": "", "value4": "", "value5": "", "Estado": ""
                })
                phone_found_in_row = True
                break # Encontramos uno válido, pasamos a la siguiente fila

            # 2. Si no hay válidos, buscar teléfonos potenciales para reportar el error
            potential_phones = potential_phone_regex.findall(cell_value)
            for phone in potential_phones:
                reason = ""
                if len(phone) != 10:
                    reason = "No tiene 10 dígitos"
                elif not phone.startswith('3'):
                    reason = "No empieza con 3 (No es celular)"
                
                if reason:
                    row_errors.add((phone, reason, cell_value))
        
        # Si terminamos de buscar en la fila y no encontramos NINGÚN válido, guardamos los errores
        if not phone_found_in_row and row_errors:
            for phone, reason, original_value in row_errors:
                error_records.append({
                    "Nombre Asociado": found_name,
                    "Numero con Error": phone,
                    "Razon del Error": reason,
                    "Valor Original en Celda": original_value
                })

    # Crear DataFrames finales
    valid_df = pd.DataFrame(valid_records).drop_duplicates(subset=['Numero telefono'], keep='first')
    error_df = pd.DataFrame(error_records).drop_duplicates()

    return valid_df, error_df

# --- Interfaz Gráfica de la Aplicación ---
st.title("📊 Generador de Bases con Reporte de Errores")
st.markdown("La herramienta ahora crea una hoja adicional en el Excel con los números que no pudo validar.")

uploaded_files = st.file_uploader("Arrastra tus archivos Excel de origen aquí", type=['xlsx', 'xls'], accept_multiple_files=True)

if uploaded_files:
    df = pd.concat([pd.read_excel(f, dtype=str) for f in uploaded_files], ignore_index=True)
    st.success(f"✅ ¡Carga completa! Se han unido {len(uploaded_files)} archivos. Total de filas: {len(df)}.")
    
    st.header("1. Configurar Búsqueda")
    all_cols = df.columns.tolist()

    # Selectores para columnas de Nombre y Teléfono
    name_keywords = ['nombre', 'name', 'tutor', 'student']; default_name_cols = [c for c in all_cols if any(k in c.lower() for k in name_keywords)]
    name_columns = st.multiselect("¿Columnas que contienen Nombres?", options=all_cols, default=default_name_cols)
    phone_keywords = ['tel', 'phone', 'grupo', 'email', 'teléfono']; default_phone_cols = [c for c in all_cols if any(k in c.lower() for k in phone_keywords)]
    phone_columns = st.multiselect("¿Columnas que contienen Teléfonos?", options=all_cols, default=default_phone_cols)

    if st.button("🚀 Generar Base y Reporte de Errores", type="primary"):
        valid_df, error_df = extract_and_format_with_error_handling(df, phone_columns, name_columns)
        
        # --- SECCIÓN DE RESULTADOS MEJORADA ---
        st.header("2. Resultados")

        # Pestaña 1: Datos Válidos
        st.subheader("Contactos Válidos (Hoja: BASE APPP)")
        if valid_df.empty:
            st.warning("No se encontraron contactos válidos con la configuración actual.")
        else:
            st.dataframe(valid_df)
            st.info(f"Se generará una base con {len(valid_df)} contactos únicos.")
        
        # Pestaña 2: Reporte de Errores
        st.subheader("Registros con Errores (Hoja: Registros con Errores)")
        if error_df.empty:
            st.success("¡Excelente! No se encontraron números con errores de formato.")
        else:
            st.dataframe(error_df)
            st.warning(f"Se encontraron {len(error_df)} números que no pudieron ser validados.")

        # --- LÓGICA DE DESCARGA MEJORADA ---
        if not valid_df.empty or not error_df.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                valid_df.to_excel(writer, index=False, sheet_name='BASE APPP')
                if not error_df.empty:
                    error_df.to_excel(writer, index=False, sheet_name='Registros con Errores')
            
            st.download_button(
                label="⬇️ Descargar Archivo Excel con Ambas Hojas",
                data=output.getvalue(),
                file_name="Resultado_Con_Reporte_De_Errores.xlsx",
                mime="application/vnd.ms-excel"
            )
