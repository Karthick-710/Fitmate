from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import csv

app = Flask(__name__)
app.secret_key = "fitness_secret"

def init_db():
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    age INTEGER,
                    weight FLOAT,
                    height FLOAT,
                    bmi FLOAT,
                    calories_consumed FLOAT,
                    protein FLOAT,
                    carbs FLOAT,
                    fat FLOAT,
                    fiber FLOAT,
                    calories_burned FLOAT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

init_db()

# Function to load foods from CSV
def load_foods():
    foods = []
    with open('foods.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            foods.append({
                "name": row["name"],
                "calories_per_100g": float(row["calories"]),
                "carbs": float(row["carbs"]),
                "protein": float(row["protein"]),
                "fat": float(row["fat"]),
                "fiber": float(row["fiber"])
            })
    return foods

# Function to load activities from CSV
def load_activities():
    activities = []
    with open('activities.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            activities.append({
                "name": row["name"],
                "calories_burned_per_min": float(row["calories_burned_per_min"])
            })
    return activities

# Load foods and activities
foods = load_foods()
activities = load_activities()

@app.route('/', methods=['GET', 'POST'])
def home():
    total_calories = total_carbs = total_protein = total_fat = total_fiber = total_burn = bmi = 0
    name = height = age = weight = " "

    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        height = float(request.form.get('height'))
        weight = float(request.form.get('weight'))

        # Calculate BMI
        bmi = round(weight / ((height / 100) ** 2), 2)

        food_items = request.form.getlist('food[]')
        food_amounts = request.form.getlist('food_amount[]')
        activity_items = request.form.getlist('activity[]')
        activity_durations = request.form.getlist('activity_duration[]')

        for food_name, amount in zip(food_items, food_amounts):
            for food in foods:
                if food['name'] == food_name:
                    factor = float(amount) / 100
                    total_calories += food['calories_per_100g'] * factor
                    total_carbs += food['carbs'] * factor
                    total_protein += food['protein'] * factor
                    total_fat += food['fat'] * factor
                    total_fiber += food['fiber'] * factor
                    break

        for activity_name, duration in zip(activity_items, activity_durations):
            for activity in activities:
                if activity['name'] == activity_name:
                    total_burn += activity['calories_burned_per_min'] * float(duration)
                    break

        # Store in database
        conn = sqlite3.connect("fitness_tracker.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO user_history 
                          (name, age, height, weight, bmi, calories_consumed, protein, carbs, fat, fiber, calories_burned) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (name, age, height, weight, bmi, total_calories, total_protein, total_carbs, total_fat, total_fiber, total_burn))
        conn.commit()
        conn.close()

    return render_template('index.html', foods=foods, activities=activities, total_calories=total_calories,
                           total_carbs=total_carbs, total_protein=total_protein, total_fat=total_fat,
                           total_fiber=total_fiber, total_burn=total_burn, bmi=bmi, name=name, age=age,
                           height=height, weight=weight)

@app.route('/history')
def history():
    conn = sqlite3.connect("fitness_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_history ORDER BY id DESC LIMIT 10")
    history_data = cursor.fetchall()
    conn.close()
    return render_template('history.html', history_data=history_data)

@app.route('/history/<user_name>')
def user_history(user_name):
    conn = sqlite3.connect('fitness_tracker.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_history WHERE name = ?", (user_name,))
    history_data = cursor.fetchall()
    conn.close()
    return render_template('user_history.html', history_data=history_data, user_name=user_name)

if __name__ == '__main__':
    app.run(debug=True)
