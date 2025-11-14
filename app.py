import streamlit as st
import requests

st.title("Asistente Inmobiliario Inteligente 🏠🤖")

st.write("Usa las herramientas de búsqueda de pisos y scoring de candidatos.")

# URLs de n8n
WEBHOOK_M4 = "https://gabrieldones.app.n8n.cloud/webhook/buscar-piso"
WEBHOOK_M5 = "https://gabrieldones.app.n8n.cloud/webhook/scoring-candidato"


# -----------------------------------
# M4 - Buscar piso
# -----------------------------------
st.header("🔎 M4 – Buscador de pisos")

busqueda = st.text_area("¿Qué piso estás buscando?", key="m4_input")

if st.button("Buscar piso"):
    if not busqueda.strip():
        st.error("Por favor escribe una búsqueda.")
    else:
        st.info("Buscando pisos…")
        response = requests.post(WEBHOOK_M4, json={"busqueda": busqueda})

        if response.status_code == 200:
            st.success("Resultados encontrados:")
            st.write(response.text)
        else:
            st.error("Error al conectar con el servidor.")
            st.write(response.text)


# -----------------------------------
# M5 – Scoring de candidato
# -----------------------------------
st.header("🧩 M5 – Scoring de candidato")

nombre = st.text_input("Nombre del candidato", key="nombre_input")
ingresos = st.number_input("Ingresos mensuales (€)", min_value=0, key="ingresos_input")
profesion = st.text_input("Profesión", key="profesion_input")
mascotas = st.selectbox("¿Mascotas?", ["No", "Sí"], key="mascotas_input")
estabilidad = st.selectbox("Estabilidad laboral", ["Indefinido", "Temporal", "Autónomo", "Paro"], key="estabilidad_input")
fumador = st.selectbox("¿Fumador?", ["No", "Sí"], key="fumador_input")
alquiler_max = st.number_input("Alquiler máximo que puede pagar (€)", min_value=0, key="alquiler_input")

if st.button("Calcular scoring"):
    datos = {
        "nombre": nombre,
        "ingresos": ingresos,
        "profesion": profesion,
        "mascotas": mascotas,
        "estabilidad_laboral": estabilidad,
        "fumador": fumador,
        "alquiler_maximo": alquiler_max
    }

    st.info("Calculando scoring…")
    response = requests.post(WEBHOOK_M5, json=datos)

    try:
        resultado = response.json()
        st.success("Resultado del scoring:")
        st.json(resultado)
    except:
        st.error("El servidor devolvió un formato inesperado.")
        st.write(response.text)


