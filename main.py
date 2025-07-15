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
        
        # Create transactions table
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
        
        # Create users table
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
        score = 50  # Base score
        
        # Savings ratio (higher is better)
        if income > 0:
            savings_ratio = savings / income
            score += min(30, savings_ratio * 100)
            debt_ratio = loans / income
            if debt_ratio > 2:  # Penalize >200% debt-to-income
                score -= 20
            score -= min(25, debt_ratio * 50)
        
        # Expense management (lower expenses relative to income is better)
        expense_ratio = expenses / income if income > 0 else 1
        if expense_ratio < 0.5:
            score += 10
        elif expense_ratio > 0.8:
            score -= 15
        else:
            score -= 20  # No income case
        
        # Absolute savings amount
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
        return max(0, min(100, 60 + (new_savings * 0.001)))  # Caps at 100
    
    def display_credit_result(self, score, savings, loans, income, expenses):
        """Display credit score results"""
        print("\n" + "="*50)
        print("📊 CREDIT ASSESSMENT RESULTS")
        print("="*50)
        print(f"🎯 Credit Score: {score:.0f}/100")
        
        if score >= 80:
            print("🟢 Excellent - Low risk borrower")
            recommendation = "Approved for loans up to R{:.0f}".format(income * 3 if income > 0 else 1000)
        elif score >= 60:
            print("🟡 Good - Moderate risk borrower")
            recommendation = "Approved for loans up to R{:.0f}".format(income * 2 if income > 0 else 1000)
        elif score >= 40:
            print("🟠 Fair - Higher risk, consider smaller amounts")
            recommendation = "Approved for loans up to R{:.0f}".format(income * 1 if income > 0 else 1000)
        else:
            print("🔴 Poor - Focus on building savings first")
            recommendation = "Recommend savings program before loans"
        
        print(f"💡 Recommendation: {recommendation}")
        
        print("\n📈 Financial Summary:")
        print(f"💰 Savings: R{savings:,.2f}")
        print(f"💸 Loans: R{loans:,.2f}")
        debt_to_income = (loans / income * 100) if income > 0 else float('inf') if loans > 0 else 0
        print(f"📊 Debt-to-Income: {debt_to_income:.1f}%")
        print(f"💾 Memory Usage: {self.get_memory_usage():.1f} MB")
        print("="*50)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    groweasy = GrowEasy()
    if request.method == 'POST':
        try:
            savings = float(request.form['savings'])
            loans = float(request.form['loans'])
            income = float(request.form['income'])
            expenses = float(request.form['expenses'])
            if any(x < 0 for x in [savings, loans, income, expenses]):
                return "❌ Error: All values must be non-negative.", 400
            score = groweasy.calculate_credit_score(savings, loans, income, expenses)
            groweasy.add_transaction("web_user", savings, loans, income, expenses)
            return render_template('result.html', score=score, savings=savings, loans=loans, income=income, expenses=expenses)
        except ValueError:
            return "❌ Please enter valid numbers.", 400
    return render_template('index.html')

@app.route('/simulate', methods=['GET', 'POST'])
def simulate():
    groweasy = GrowEasy()
    if request.method == 'POST':
        try:
            savings = float(request.form['savings'])
            months = int(request.form['months'])
            monthly_save = float(request.form['monthly_save'])
            if any(x < 0 for x in [savings, monthly_save]) or months < 0:
                return "❌ Error: Values must be non-negative and months non-negative.", 400
            future_score = groweasy.simulate_growth(savings, months, monthly_save)
            return render_template('simulate_result.html', future_score=future_score, months=months, monthly_save=monthly_save)
        except ValueError:
            return "❌ Please enter valid numbers.", 400
    return render_template('simulate.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)