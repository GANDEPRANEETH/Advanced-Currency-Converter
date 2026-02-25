from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "converter.db"


# Initialize Database

def init_db():
    conn = sqlite3.connect("converter.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            result REAL NOT NULL,
            rate REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()


# Home Route

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None
    rate_value = None

    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            from_currency = request.form["from_currency"].upper()
            to_currency = request.form["to_currency"].upper()

            if amount <= 0:
                error = "Amount must be greater than 0"
            else:
                url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
                response = requests.get(url)
                data = response.json()

                if "rates" not in data:
                    error = "Invalid Base Currency!"
                else:
                    rate_value = data["rates"].get(to_currency)

                    if rate_value is None:
                        error = "Invalid Target Currency!"
                    else:
                        result = round(amount * rate_value, 2)

                        # Save to DB
                        conn = sqlite3.connect(DATABASE)
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO history (amount, from_currency, to_currency, result, rate, date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            amount,
                            from_currency,
                            to_currency,
                            result,
                            rate_value,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                        conn.commit()
                        conn.close()

        except Exception:
            error = "Something went wrong. Please check inputs."
    try:
        currency_url = "https://api.exchangerate-api.com/v4/latest/USD"
        currency_response = requests.get(currency_url)
        currency_data = currency_response.json()
        currencies = sorted(currency_data["rates"].keys())
    except:
        currencies = ["USD", "INR", "EUR", "GBP"]
    return render_template(
        "index.html",
        result=result,
        error=error,
        rate=rate_value,
        currencies = currencies
    )


# -------------------------------
# History Route
# -------------------------------
@app.route("/history")
def history():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY id DESC")
    records = cursor.fetchall()
    conn.close()

    return render_template("history.html", records=records)



# Run App
if __name__ == "__main__":
    app.run(debug=True)