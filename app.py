import streamlit as st
import requests
import json
import re

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

            # Mostrar solo texto limpio del modelo
            try:
                data = response.json()
                texto = data["output"][0]["content"][0]["text"]
                st.write(texto)
            except:
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
        # 1. Capturar la respuesta JSON completa
        data = response.json()

        # 2. Extraer el texto generado por el modelo
        texto = data["data"]["output"][0]["content"][0]["text"]

        # 3. Limpiar bloques ```json ... ```
        texto_limpio = texto.replace("```json", "").replace("```", "").strip()

        # 4. Convertir a JSON válido
        resultado_json = json.loads(texto_limpio)

        # 5. Mostrar JSON bonito
        st.success("Resultado del scoring:")
        st.json(resultado_json)

    except Exception as e:
        st.error("El servidor devolvió un formato inesperado.")
        st.write("Respuesta completa (debug):")
        st.write(response.text)
        st.write(str(e))
