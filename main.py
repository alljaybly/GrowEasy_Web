from flask import Flask, request, render_template
import sqlite3
import os
import time
from datetime import datetime
import psutil

class GrowEasy:
    def __init__(self):
        """Initialize GrowEasy microfinance app"""
        self.db_name = 'groweasy.db'
        self.setup_database()
        print("✅ GrowEasy initialized successfully")
    
    def setup_database(self):
        """Setup SQLite database for offline storage"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                savings REAL NOT NULL,
                loans REAL NOT NULL,
                income REAL NOT NULL,
                expenses REAL NOT NULL,
                timestamp TEXT NOT NULL,
                synced INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                group_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def calculate_credit_score(self, savings, loans, income, expenses):
        """Calculate credit score using rule-based algorithm"""
        score = 50
        if income > 0:
            savings_ratio = savings / income
            score += min(30, savings_ratio * 100)
            debt_ratio = loans / income
            if debt_ratio > 2:
                score -= 20
            score -= min(25, debt_ratio * 50)
            expense_ratio = expenses / income
            if expense_ratio < 0.5:
                score += 10
            elif expense_ratio > 0.8:
                score -= 15
        else:
            score -= 20
        if savings > 1000:
            score += 10
        elif savings > 500:
            score += 5
        return max(0, min(100, score))
    
    def add_user(self, user_id, name, phone="", group_name=""):
        """Add new user to the system"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, name, phone, group_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, phone, group_name, datetime.now().isoformat()))
            conn.commit()
            print(f"✅ User {name} added successfully")
            return True
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            return False
        finally:
            conn.close()
    
    def add_transaction(self, user_id, savings, loans, income, expenses):
        """Add new transaction to local database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO transactions (user_id, savings, loans, income, expenses, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, savings, loans, income, expenses, datetime.now().isoformat()))
            conn.commit()
            print("✅ Transaction saved locally")
            return True
        except Exception as e:
            print(f"❌ Error saving transaction: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_history(self, user_id):
        """Get transaction history for a user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT savings, loans, income, expenses, timestamp
            FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (user_id,))
        history = cursor.fetchall()
        conn.close()
        return history
    
    def simulate_wifi_sync(self):
        """Simulate Wi-Fi synchronization with cloud server"""
        print("\n🔄 Starting Wi-Fi sync simulation...")
        time.sleep(1)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE synced = 0')
        unsynced_count = cursor.fetchone()[0]
        if unsynced_count == 0:
            print("✅ All data is already synced")
            conn.close()
            return
        print(f"📤 Found {unsynced_count} unsynced transactions")
        for i in range(3):
            print(f"📡 Syncing... {((i+1)/3)*100:.0f}%")
            time.sleep(0.5)
        cursor.execute('UPDATE transactions SET synced = 1 WHERE synced = 0')
        conn.commit()
        conn.close()
        with open('sync_log.txt', 'a') as f:
            f.write(f"{datetime.now().isoformat()}: Synced {unsynced_count} transactions\n")
        print("✅ Sync completed successfully!")
        print(f"📊 {unsynced_count} transactions uploaded to cloud")
    
    def get_memory_usage(self):
        """Get current memory usage for monitoring"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb
    
    def simulate_growth(self, savings, months, monthly_save):
        """Simulate future credit score based on savings growth"""
        new_savings = savings + (monthly_save * months)
        return max(0, min(100, 60 + (new_savings * 0.001)))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index_menu.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    groweasy = GrowEasy()
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['name']
        phone = request.form['phone']
        group_name = request.form['group_name']
        groweasy.add_user(user_id, name, phone, group_name)
        return render_template('success.html', message=f"User {name} added successfully!")
    return render_template('add_user.html')

@app.route('/credit_assessment', methods=['GET', 'POST'])
def credit_assessment():
    groweasy = GrowEasy()
    if request.method == 'POST':
        user_id = request.form['user_id']
        savings = float(request.form['savings'])
        loans = float(request.form['loans'])
        income = float(request.form['income'])
        expenses = float(request.form['expenses'])
        if any(x < 0 for x in [savings, loans, income, expenses]):
            return "❌ Error: All values must be non-negative.", 400
        score = groweasy.calculate_credit_score(savings, loans, income, expenses)
        groweasy.add_transaction(user_id, savings, loans, income, expenses)
        return render_template('result.html', score=score, savings=savings, loans=loans, income=income, expenses=expenses, user_id=user_id)
    return render_template('credit_assessment.html')

@app.route('/view_history', methods=['GET', 'POST'])
def view_history():
    groweasy = GrowEasy()
    if request.method == 'POST':
        user_id = request.form['user_id']
        history = groweasy.get_user_history(user_id)
        if not history:
            return render_template('history.html', history=None, user_id=user_id, message="No history found for this user.")
        return render_template('history.html', history=history, user_id=user_id)
    return render_template('view_history.html')
@app.route('/sync', methods=['GET'])
def sync():
    groweasy = GrowEasy()
    groweasy.simulate_wifi_sync()
    return "Sync completed! <a href='/'>Back to Menu</a>"

@app.route('/status', methods=['GET'])
def status():
    groweasy = GrowEasy()
    memory_mb = groweasy.get_memory_usage()
    conn = sqlite3.connect(groweasy.db_name)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM transactions')
    transaction_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE synced = 0')
    unsynced_count = cursor.fetchone()[0]
    conn.close()
    db_size = os.path.getsize(groweasy.db_name) / 1024 if os.path.exists(groweasy.db_name) else 0
    return render_template('status.html', memory_mb=memory_mb, user_count=user_count, transaction_count=transaction_count, unsynced_count=unsynced_count, db_size=db_size)

@app.route('/simulate', methods=['GET', 'POST'])
def simulate():
    groweasy = GrowEasy()
    if request.method == 'POST':
        savings = float(request.form['savings'])
        months = int(request.form['months'])
        monthly_save = float(request.form['monthly_save'])
        if any(x < 0 for x in [savings, monthly_save]) or months < 0:
            return "❌ Error: Values must be non-negative and months non-negative.", 400
        future_score = groweasy.simulate_growth(savings, months, monthly_save)
        return render_template('simulate_result.html', future_score=future_score, months=months, monthly_save=monthly_save)
    return render_template('simulate.html')

@app.route('/exit', methods=['GET'])
def exit_app():
    return "Thank you for using GrowEasy! <a href='/'>Return to Menu</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)