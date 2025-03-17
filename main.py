import streamlit as st
import requests
import json
import matplotlib.pyplot as plt

# URL del file JSON su GitHub (versione RAW)
GITHUB_JSON_URL = "https://raw.githubusercontent.com/FrancDeps/food_nutrition_calculator/main/nutritional_data.json"

# Funzione per scaricare il database da GitHub
@st.cache_data
def carica_dati():
    try:
        response = requests.get(GITHUB_JSON_URL)
        response.raise_for_status()  # Controlla errori HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return {}

# Carica il database
DATABASE_ALIMENTI = carica_dati()

# Inizializza Session State per salvare gli alimenti selezionati
if "storico_alimenti" not in st.session_state:
    st.session_state.storico_alimenti = {}

st.title("🍏 Nutritional Tracker")

alimento = st.text_input("Inserisci il nome dell'alimento:")
quantita = st.number_input("Inserisci la quantità in grammi:", min_value=1, value=100)

if st.button("Aggiungi alimento"):
    alimento = alimento.lower()
    if alimento in DATABASE_ALIMENTI:
        valori_base = DATABASE_ALIMENTI[alimento]
        proporzione = quantita / 100
        
        valori = {
            "calorie": valori_base["calorie"] * proporzione,
            "proteine": valori_base["proteine"] * proporzione,
            "carboidrati": valori_base["carboidrati"] * proporzione,
            "grassi": valori_base["grassi"] * proporzione,
            "quantita": quantita
        }
        
        st.session_state.storico_alimenti[alimento] = valori
        st.success(f"Aggiunto {quantita}g di {alimento}")
    else:
        st.error("❌ Alimento non trovato nel database.")

# Calcola i totali
tot_calorie = sum(v["calorie"] for v in st.session_state.storico_alimenti.values())
tot_proteine = sum(v["proteine"] for v in st.session_state.storico_alimenti.values())
tot_carboidrati = sum(v["carboidrati"] for v in st.session_state.storico_alimenti.values())
tot_grassi = sum(v["grassi"] for v in st.session_state.storico_alimenti.values())

# Mostra i totali
st.header("📊 Totale valori nutrizionali")
st.write(f"**Totale Calorie:** {tot_calorie:.2f} kcal")
st.write(f"**Totale Proteine:** {tot_proteine:.2f} g")
st.write(f"**Totale Carboidrati:** {tot_carboidrati:.2f} g")
st.write(f"**Totale Grassi:** {tot_grassi:.2f} g")

# Grafico a torta
st.header("🥧 Distribuzione Macronutrienti")
fig, ax = plt.subplots(figsize=(6, 6))
labels = ["Proteine", "Carboidrati", "Grassi"]
values = [tot_proteine, tot_carboidrati, tot_grassi]
ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=["blue", "orange", "red"])
st.pyplot(fig)

# Confronto con benchmark calorico
benchmark_calorie = 2000
surplus_deficit = tot_calorie - benchmark_calorie
st.header("⚖️ Confronto con benchmark calorico")
if surplus_deficit > 0:
    st.warning(f"🔥 Sei in surplus calorico di {surplus_deficit:.2f} kcal.")
elif surplus_deficit < 0:
    st.info(f"🥗 Sei in deficit calorico di {abs(surplus_deficit):.2f} kcal.")
else:
    st.success("✅ Sei esattamente a 2000 kcal.")
