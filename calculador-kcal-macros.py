import streamlit as st
import plotly.express as px
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Título y descripción
st.title("Calculadora de Calorías y Macronutrientes")
st.markdown("Ingresa tus datos para calcular tus necesidades calóricas y macronutrientes según tus objetivos.")

# Base de datos de alimentos (kcal, proteínas, carbohidratos, grasas por 100 g)
food_database = {
    "Pollo (pechuga)": {"kcal": 165, "protein": 31, "carb": 0, "fat": 3.6},
    "Arroz blanco": {"kcal": 130, "protein": 2.7, "carb": 28, "fat": 0.3},
    "Aguacate": {"kcal": 160, "protein": 2, "carb": 9, "fat": 15},
    "Huevo cocido": {"kcal": 155, "protein": 13, "carb": 1.1, "fat": 11},
    "Yogur natural (entero)": {"kcal": 61, "protein": 3.5, "carb": 4.7, "fat": 3.3},
    "Mantequilla de maní": {"kcal": 588, "protein": 25, "carb": 20, "fat": 50},
    "Plátano": {"kcal": 89, "protein": 1.1, "carb": 23, "fat": 0.3},
    "Brócoli": {"kcal": 35, "protein": 2.8, "carb": 7, "fat": 0.4},
    "Aceite de oliva": {"kcal": 884, "protein": 0, "carb": 0, "fat": 100},
    "Pan integral": {"kcal": 247, "protein": 9, "carb": 41, "fat": 3.5},
}

# Función para generar sugerencias de comidas
def suggest_meal(calories, protein, carb, fat):
    meal_suggestion = []
    remaining_calories, remaining_protein, remaining_carb, remaining_fat = calories, protein, carb, fat
    
    # Priorizar una fuente de proteína
    protein_foods = [f for f, v in food_database.items() if v["protein"] > 10]
    for food in protein_foods:
        if remaining_protein > 0:
            grams = min(100, remaining_protein * 100 / food_database[food]["protein"])
            meal_suggestion.append(f"{grams:.1f} g de {food}")
            remaining_calories -= grams * food_database[food]["kcal"] / 100
            remaining_protein -= grams * food_database[food]["protein"] / 100
            remaining_carb -= grams * food_database[food]["carb"] / 100
            remaining_fat -= grams * food_database[food]["fat"] / 100
            break
    
    # Agregar carbohidratos
    carb_foods = [f for f, v in food_database.items() if v["carb"] > 10]
    for food in carb_foods:
        if remaining_carb > 0 and remaining_calories > 0:
            grams = min(100, remaining_carb * 100 / food_database[food]["carb"])
            meal_suggestion.append(f"{grams:.1f} g de {food}")
            remaining_calories -= grams * food_database[food]["kcal"] / 100
            remaining_protein -= grams * food_database[food]["protein"] / 100
            remaining_carb -= grams * food_database[food]["carb"] / 100
            remaining_fat -= grams * food_database[food]["fat"] / 100
            break
    
    # Agregar grasas
    fat_foods = [f for f, v in food_database.items() if v["fat"] > 10]
    for food in fat_foods:
        if remaining_fat > 0 and remaining_calories > 0:
            grams = min(20, remaining_fat * 100 / food_database[food]["fat"])
            meal_suggestion.append(f"{grams:.1f} g de {food}")
            break
    
    return ", ".join(meal_suggestion) if meal_suggestion else "Ajusta las cantidades manualmente."

# Función para generar PDF
def generate_pdf(name, calories, protein_g, carb_g, fat_g, meal_plan):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    y = 750
    
    c.drawString(50, y, f"Plan Nutricional Personalizado para {name}")
    y -= 30
    c.drawString(50, y, f"Calorías diarias: {int(calories)} kcal")
    y -= 20
    c.drawString(50, y, f"Proteínas: {int(protein_g)} g")
    c.drawString(200, y, f"Carbohidratos: {int(carb_g)} g")
    c.drawString(350, y, f"Grasas: {int(fat_g)} g")
    y -= 30
    
    c.drawString(50, y, "Distribución por comidas:")
    y -= 20
    for meal, data in meal_plan.items():
        c.drawString(50, y, f"{meal}: {int(data['calories'])} kcal (P: {int(data['protein'])} g, C: {int(data['carb'])} g, G: {int(data['fat'])} g)")
        y -= 20
        c.drawString(70, y, f"Sugerencia: {data['suggestion']}")
        y -= 20
        if y < 50:
            c.showPage()
            y = 750
    
    c.save()
    buffer.seek(0)
    return buffer

# Formulario
with st.form("calorie_form"):
    st.subheader("Datos del usuario")
    name = st.text_input("Nombre", placeholder="Ej. Miguel o Emma")
    user_type = st.selectbox("¿Eres adulto o niño?", ["Adulto", "Niño"])
    age = st.number_input("Edad (años)", min_value=0, max_value=120, step=1)
    sex = st.selectbox("Sexo", ["Hombre", "Mujer"])
    weight = st.number_input("Peso (kg)", min_value=1.0, step=0.1)
    height = st.number_input("Altura (cm)", min_value=30.0, step=0.1)
    activity_level = st.selectbox("Nivel de actividad", ["Sedentario", "Moderado", "Activo", "Muy activo"])
    if user_type == "Adulto":
        goal = st.selectbox("Objetivo", ["Bajar de peso", "Mantener peso", "Subir de peso"])
    else:
        goal = st.selectbox("Objetivo", ["Crecimiento"])
        low_weight = st.checkbox("¿Está bajo de peso?")
    meals_per_day = st.selectbox("Número de comidas diarias", [3, 4, 5, 6])
    submit_button = st.form_submit_button("Calcular")

# Lógica de cálculo
if submit_button:
    if weight <= 0 or height <= 0 or age < 0:
        st.error("Por favor, ingresa valores válidos para peso, altura y edad.")
    else:
        # Factores de actividad
        activity_factors = {"Sedentario": 1.2, "Moderado": 1.4, "Activo": 1.6, "Muy activo": 1.8}
        
        # Calcular TMB
        if user_type == "Niño":
            if age < 3:
                tmb = (58.317 if sex == "Mujer" else 59.512) * weight - (31.1 if sex == "Mujer" else 30.4)
            elif age < 10:
                tmb = (20.315 if sex == "Mujer" else 22.706) * weight + (485.9 if sex == "Mujer" else 504.3) * (height / 100) + (26.9 if sex == "Mujer" else 20.3)
            else:
                tmb = (13.384 if sex == "Mujer" else 17.686) * weight + (692.6 if sex == "Mujer" else 658.2) * (height / 100) + (112.8 if sex == "Mujer" else 15.1)
        else:
            # Fórmula Mifflin-St Jeor para adultos
            if sex == "Mujer":
                tmb = (10 * weight) + (6.25 * height) - (5 * age) - 161
            else:
                tmb = (10 * weight) + (6.25 * height) - (5 * age) + 5

        # Calorías totales
        calories = tmb * activity_factors[activity_level]
        
        # Ajustar por objetivo
        if goal == "Bajar de peso":
            calories *= 0.85
        elif goal == "Subir de peso" or (user_type == "Niño" and low_weight):
            calories *= 1.15

        # Macronutrientes
        if user_type == "Niño":
            protein_pct = 0.2 if low_weight else 0.15
            carb_pct = 0.55
            fat_pct = 0.3
            protein_g_per_kg = 1.5 if low_weight else 1.1
        else:
            protein_pct = 0.25 if goal == "Subir de peso" else 0.2
            carb_pct = 0.5
            fat_pct = 0.3
            protein_g_per_kg = 2.0 if goal == "Subir de peso" else 1.6 if goal == "Bajar de peso" else 1.2

        protein_g = max(weight * protein_g_per_kg, calories * protein_pct / 4)
        carb_g = calories * carb_pct / 4
        fat_g = calories * fat_pct / 9

        # Distribución por comidas
        main_meals = ["Desayuno", "Almuerzo", "Cena"][:min(3, meals_per_day)]
        snacks = ["Media mañana", "Merienda", "Colación"][:max(0, meals_per_day - 3)]
        main_meal_calories = calories * 0.6 / len(main_meals)
        snack_calories = calories * 0.4 / len(snacks) if snacks else 0

        meal_plan = {}
        for meal in main_meals:
            meal_plan[meal] = {
                "calories": main_meal_calories,
                "protein": protein_g * 0.6 / len(main_meals),
                "carb": carb_g * 0.6 / len(main_meals),
                "fat": fat_g * 0.6 / len(main_meals),
                "suggestion": suggest_meal(main_meal_calories, protein_g * 0.6 / len(main_meals), carb_g * 0.6 / len(main_meals), fat_g * 0.6 / len(main_meals))
            }
        for snack in snacks:
            meal_plan[snack] = {
                "calories": snack_calories,
                "protein": protein_g * 0.4 / len(snacks),
                "carb": carb_g * 0.4 / len(snacks),
                "fat": fat_g * 0.4 / len(snacks),
                "suggestion": suggest_meal(snack_calories, protein_g * 0.4 / len(snacks), carb_g * 0.4 / len(snacks), fat_g * 0.4 / len(snacks))
            }

        # Mostrar resultados
        st.subheader(f"Resultados para {name if name else 'ti'}")
        st.write(f"¡{'Aquí está tu plan, ' + name + '!' if name else '¡Tu plan está listo!'}")
        st.write(f"**Calorías diarias estimadas:** {int(calories)} kcal")
        st.write(f"**Proteínas:** {int(protein_g)} g ({protein_pct*100:.0f}%)")
        st.write(f"**Carbohidratos:** {int(carb_g)} g ({carb_pct*100:.0f}%)")
        st.write(f"**Grasas:** {int(fat_g)} g ({fat_pct*100:.0f}%)")

        # Gráfico de macronutrientes
        macro_df = pd.DataFrame({
            "Macronutriente": ["Proteínas", "Carbohidratos", "Grasas"],
            "Gramos": [protein_g, carb_g, fat_g]
        })
        fig = px.pie(macro_df, values="Gramos", names="Macronutriente", title="Distribución de Macronutrientes")
        st.plotly_chart(fig)

        # Distribución por comidas
        st.subheader("Distribución por comidas")
        for meal, data in meal_plan.items():
            with st.expander(f"{meal} ({int(data['calories'])} kcal)"):
                st.write(f"Proteínas: {int(data['protein'])} g, Carbohidratos: {int(data['carb'])} g, Grasas: {int(data['fat'])} g")
                st.write(f"**Sugerencia de comida:** {data['suggestion']}")

        # Generar y ofrecer PDF
        pdf_buffer = generate_pdf(name if name else "Usuario", calories, protein_g, carb_g, fat_g, meal_plan)
        st.download_button(
            label="Descarga tu plan en PDF",
            data=pdf_buffer,
            file_name=f"plan_nutricional_{name if name else 'usuario'}.pdf",
            mime="application/pdf"
        )
