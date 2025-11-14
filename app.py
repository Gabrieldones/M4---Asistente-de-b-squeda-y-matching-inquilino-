import streamlit as st
import requests

st.title("Buscador de Pisos Inteligente 🏠🤖")

st.write("Describe qué piso buscas y el asistente te devolverá opciones y un resumen inteligente.")

# Input del usuario
busqueda = st.text_area("¿Qué piso estás buscando?")

# Webhook de producción n8n
WEBHOOK_URL = "https://gabrieldones.app.n8n.cloud/webhook/buscar-piso"

if st.button("Buscar piso"):
    if not busqueda.strip():
        st.error("Por favor escribe una búsqueda.")
    else:
        st.info("Buscando...")

        try:
            # Mandar la búsqueda a n8n
            response = requests.post(WEBHOOK_URL, json={"busqueda": busqueda})

            if response.status_code == 200:
                resultado = response.text  # n8n responde en texto
                st.success("Aquí tienes las opciones encontradas:")
                st.write(resultado)
            else:
                st.error(f"Error del servidor: {response.status_code}")
                st.write(response.text)

        except Exception as e:
            st.error("Error al conectar con n8n.")
            st.write(str(e))

