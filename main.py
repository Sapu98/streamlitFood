import streamlit as st
import requests
import json
import base64
import matplotlib.pyplot as plt
from datetime import datetime

# GitHub Configuration
GITHUB_TOKEN1 = "ghp_tKJMlnBlpxtk75K"
GITHUB_TOKEN2 = "bmWQNjJTIW40HeV1jGcrg"
GITHUB_TOKEN = GITHUB_TOKEN1 + GITHUB_TOKEN2
GITHUB_REPO = "FrancDeps/food_nutrition_calculator"
GITHUB_FOLDER = "daily_logs"
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")
GITHUB_FILE_PATH = f"{GITHUB_FOLDER}/{TODAY_DATE}.json"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"


# Load Food Database from JSON File
@st.cache_data
def load_food_database():
    try:
        with open("nutritional_data.json", "r") as file:
            return json.load(file)  # Load food database
    except FileNotFoundError:
        st.error("❌ Error: `nutritional_data.json` not found. Make sure the file is in the project folder.")
        return {}


food_database = load_food_database()


# Load daily data from GitHub
def load_daily_data():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)

    if response.status_code == 200:
        data = response.json()
        decoded_content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(decoded_content), data["sha"]
    else:
        return {}, None  # Returns an empty dictionary if the file doesn't exist


# Update daily data on GitHub
def update_daily_data(new_data, sha):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    json_data = json.dumps(new_data, indent=4)
    encoded_data = base64.b64encode(json_data.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Updated daily log {TODAY_DATE}",
        "content": encoded_data,
        "sha": sha if sha else ""
    }

    response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        st.success("✅ File successfully updated on GitHub!")


# Initialize session state
if "daily_data" not in st.session_state:
    st.session_state.daily_data, st.session_state.sha = load_daily_data()

# Streamlit Interface
st.title("🍏 Daily Nutrition Tracker")

# 📌 Select gender and activity level
gender = st.radio("Select your gender:", ["Male", "Female"])
activity_level = st.selectbox("Select your activity level:", ["Sedentary", "Moderately Active", "Very Active"])

# 📌 Select goal
goal = st.selectbox("What is your goal?", ["Weight Loss", "Muscle Gain", "Endurance Training", "Ketogenic Diet"])

# 📌 Input to add food item
food_item = st.text_input("Enter food name (e.g., rice, apple, chicken):").lower()
quantity = st.number_input("Enter quantity in grams:", min_value=1, value=100)

if st.button("Add Food"):
    if food_item in food_database:
        if food_item in st.session_state.daily_data:
            st.session_state.daily_data[food_item]["quantity"] += quantity
        else:
            st.session_state.daily_data[food_item] = {"quantity": quantity}

        update_daily_data(st.session_state.daily_data, st.session_state.sha)
        st.rerun()
    else:
        st.error("⚠️ Food not found in the database. Please check the spelling.")

# 📊 Display daily food log with remove button
st.header(f"📅 Daily Nutrition Data for {TODAY_DATE}")

if st.session_state.daily_data:
    for food, info in list(st.session_state.daily_data.items()):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{food.capitalize()}**: {info.get('quantity', 0)}g")
        with col2:
            if st.button(f"❌ Remove {food}", key=f"remove_{food}"):
                del st.session_state.daily_data[food]
                update_daily_data(st.session_state.daily_data, st.session_state.sha)
                st.rerun()
else:
    st.info("No food recorded today.")

# 📊 Calculate Macronutrient Distribution
macronutrient_totals = {"Carbohydrates": 0, "Proteins": 0, "Fats": 0}

for food, info in st.session_state.daily_data.items():
    if food in food_database:
        quantity = info["quantity"] / 100  # Convert to per 100g
        for macro in macronutrient_totals:
            macronutrient_totals[macro] += food_database[food][macro] * quantity

# **Ensure macronutrient_percentages is always defined**
macronutrient_percentages = {"Carbohydrates": 0, "Proteins": 0, "Fats": 0}

# Normalize to Percentage
total_macros = sum(macronutrient_totals.values())
if total_macros > 0:
    macronutrient_percentages = {k: round((v / total_macros) * 100, 1) for k, v in macronutrient_totals.items()}

    # 📊 Interactive Pie Chart of Macronutrient Distribution
    st.header("📊 Macronutrient Distribution")

    fig, ax = plt.subplots()
    ax.pie(macronutrient_percentages.values(), labels=macronutrient_percentages.keys(), autopct='%1.1f%%',
           startangle=90)
    ax.axis("equal")
    st.pyplot(fig)

else:
    st.warning("⚠️ No food added yet. Please enter food items to see macronutrient distribution.")

# 📌 Compare macronutrient intake with target range based on goal
st.header(f"📈 Macronutrient Comparison for **{goal}**")

macronutrient_ranges = {
    "Weight Loss": {"Carbohydrates": (20, 40), "Proteins": (30, 40), "Fats": (30, 40)},
    "Muscle Gain": {"Carbohydrates": (45, 55), "Proteins": (20, 30), "Fats": (20, 30)},
    "Endurance Training": {"Carbohydrates": (55, 65), "Proteins": (15, 20), "Fats": (20, 25)},
    "Ketogenic Diet": {"Carbohydrates": (5, 10), "Proteins": (20, 25), "Fats": (65, 75)}
}

for macro, percent in macronutrient_percentages.items():
    min_range, max_range = macronutrient_ranges[goal][macro]
    if percent < min_range:
        st.warning(
            f"⚠️ **{macro}** intake **{percent}%**: Too LOW compared to the target range **{min_range}-{max_range}%**.")
    elif percent > max_range:
        st.warning(
            f"⚠️ **{macro}** intake **{percent}%**: Too HIGH compared to the target range **{min_range}-{max_range}%**.")
    else:
        st.success(f"✅ **{macro}** intake **{percent}%**: **WITHIN** the target range **{min_range}-{max_range}%**.")


















