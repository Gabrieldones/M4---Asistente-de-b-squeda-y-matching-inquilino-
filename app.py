# app.py
import streamlit as st
import pandas as pd
import os
import requests

# Intentamos usar OpenAI si la clave está en secrets
USE_OPENAI = False
OPENAI_KEY = None
try:
    OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
    if OPENAI_KEY and OPENAI_KEY.strip() != "":
        USE_OPENAI = True
except Exception:
    USE_OPENAI = False

# Opcional: webhook n8n (si lo configuras en secrets)
N8N_WEBHOOK = None
try:
    N8N_WEBHOOK = st.secrets.get("N8N_WEBHOOK", None)
except Exception:
    N8N_WEBHOOK = None

st.set_page_config(page_title="RentMatch AI - M4", page_icon="🏠", layout="centered")
st.title("🏠 RentMatch AI — Asistente de búsqueda (M4)")
st.write("Escribe lo que buscas (lenguaje natural) y te doy opciones. Si tienes OpenAI, la IA interpretará mejor; si no, se usará un matching con un CSV de ejemplo.")

# Cargar dataset de ejemplo (archivo incluido en el repo)
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("sample_pisos.csv")
    except Exception:
        # tabla vacía si no existe
        df = pd.DataFrame(columns=["id","titulo","zona","precio","num_hab","m2","desc"])
    return df

df_pisos = load_data()

query = st.text_area("🗣️ Describe lo que buscas", placeholder="Ej. Piso 2 habitaciones, luminoso, cerca del metro, Madrid Centro, <=1200€")
match_count = st.slider("Número de resultados a mostrar", 1, 6, 3)

if st.button("Buscar"):
    if not query or query.strip() == "":
        st.warning("Por favor escribe lo que buscas.")
    else:
        with st.spinner("Procesando tu búsqueda..."):
            # Si tenemos OpenAI, pedir interpretación (slots/atributos)
            if USE_OPENAI:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=OPENAI_KEY)
                    prompt = (
                        "Eres un asistente que extrae criterios de búsqueda para pisos. "
                        "Extrae: zona (o barrio), max_precio, num_hab (si aplica) y etiquetas (luminoso, balcón, ascensor, mascotas). "
                        f"Usuario dice: {query}\n"
                        "Devuelve JSON con keys: zona, max_precio, num_hab, etiquetas (lista)."
                    )
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role":"system","content":"Eres un extractor de criterios inmobiliarios."},
                            {"role":"user","content":prompt}
                        ],
                        temperature=0
                    )
                    text = resp.choices[0].message.content
                    # Intentamos parsear JSON desde la respuesta
                    import json, re
                    # Buscar primer { ... } en respuesta
                    m = re.search(r"\{.*\}", text, re.S)
                    if m:
                        parsed = json.loads(m.group(0))
                    else:
                        parsed = {}
                except Exception as e:
                    st.error("Error usando OpenAI: " + str(e))
                    parsed = {}
            else:
                parsed = {}

            # Si no hay OpenAI o parsing falla, hacemos una extracción simple por heurística
            zona = parsed.get("zona", "")
            try:
                max_precio = int(parsed.get("max_precio")) if parsed.get("max_precio") else None
            except:
                max_precio = None
            try:
                num_hab = int(parsed.get("num_hab")) if parsed.get("num_hab") else None
            except:
                num_hab = None
            etiquetas = parsed.get("etiquetas", []) if isinstance(parsed.get("etiquetas", []), list) else []

            if not USE_OPENAI:
                # heurística simple: buscar números y palabras clave en la query
                qlow = query.lower()
                # precio
                import re
                m = re.search(r'(\d{3,4})\s*€', qlow)
                if m and max_precio is None:
                    max_precio = int(m.group(1))
                # habitaciones
                m2 = re.search(r'(\d+)\s*(hab|habitación|habitaciones)', qlow)
                if m2 and num_hab is None:
                    num_hab = int(m2.group(1))
                # zona: tomar palabra 'en <zona>'
                m3 = re.search(r'en\s+([a-záéíóúñ ]{3,40})', qlow)
                if m3 and not zona:
                    zona = m3.group(1).strip()
                # etiquetas
                for k in ["luminos", "balc", "ascensor", "mascot", "terraza", "reform"]:
                    if k in qlow and k not in etiquetas:
                        etiquetas.append(k)

            # Filtrar dataset
            df = df_pisos.copy()
            if zona:
                df = df[df["zona"].str.lower().str.contains(zona.lower(), na=False)]
            if max_precio:
                df = df[df["precio"] <= max_precio]
            if num_hab:
                df = df[df["num_hab"] == num_hab]
            # score básico por coincidencia de etiquetas en descripción
            def score_row(r):
                s = 0
                text = (str(r.get("desc","")) + " " + str(r.get("titulo",""))).lower()
                for et in etiquetas:
                    if et and et.lower()[:4] in text:
                        s += 1
                # añadir proximidad precio
                if max_precio:
                    diff = max_precio - r.get("precio", max_precio)
                    if diff >= 0:
                        s += 0.5
                return s
            if not df.empty:
                df["score"] = df.apply(score_row, axis=1)
                df = df.sort_values(by="score", ascending=False)
                results = df.head(match_count)
            else:
                results = df

            # Mostrar resultados
            if results.empty:
                st.info("No se han encontrado resultados con esos criterios. Prueba ampliar zona o presupuesto.")
            else:
                for _, row in results.iterrows():
                    st.markdown(f"**{row['titulo']}** — {row['zona']} — {row['precio']}€ — {row['num_hab']} hab — {row['m2']} m²")
                    st.write(row['desc'])
                    st.markdown("---")

            # Enviar a n8n si webhook configurado (opcional)
            if N8N_WEBHOOK:
                try:
                    payload = {"query": query, "parsed": parsed, "n_results": len(results)}
                    requests.post(N8N_WEBHOOK, json=payload, timeout=5)
                except Exception as e:
                    st.warning("No se pudo enviar a n8n: " + str(e))

st.caption("Demo M4 — rentmatch.ai — versión de ejemplo")
