import os
import time
from datetime import datetime
import psutil
import psycopg2
import sqlite3
from flask import Flask, request, render_template, jsonify
import logging
import socket

# Configure logging
logging.basicConfig(filename='groweasy.log', level=logging.INFO)

class GrowEasy:
    def __init__(self):
        """Initialize GrowEasy with SQLite for offline and Postgres for online"""
        self.db_url = os.environ.get('DATABASE_URL', 'postgresql://groweasy_web_user:DgIu3tONEj7gN7QAyQDPLUo1KkwPpkY8@dpg-d1rvoa6r433s73b875g0-a.oregon-postgres.render.com/groweasy_web')
        self.local_db = 'groweasy_local.db'
        self.is_online = self.check_internet()
        self.setup_databases()
        print("✅ GrowEasy initialized successfully")

    def check_internet(self):
        """Check if internet is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except (socket.timeout, socket.error):
            return False

    def setup_databases(self):
        """Setup both local SQLite and remote PostgreSQL databases"""
        # Local SQLite setup
        with sqlite3.connect(self.local_db) as conn:
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
            logging.info("Local SQLite database initialized")

        # Remote Postgres setup only if online
        if self.is_online:
            try:
                conn = psycopg2.connect(self.db_url)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
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
                logging.info("Remote PostgreSQL database verified")
            except psycopg2.Error as e:
                logging.warning(f"Remote database setup skipped due to error: {e}")
            finally:
                conn.close()

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
        """Add new user to local database, sync if online"""
        success = False
        try:
            with sqlite3.connect(self.local_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, name, phone, group_name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, name, phone, group_name, datetime.now().isoformat()))
                conn.commit()
                logging.info(f"User {name} added locally for user_id {user_id}")
                success = True
        except sqlite3.Error as e:
            logging.error(f"Local user add error: {e}")
            return False

        if self.is_online:
            try:
                conn = psycopg2.connect(self.db_url)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, name, phone, group_name, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET name = EXCLUDED.name,
                        phone = EXCLUDED.phone,
                        group_name = EXCLUDED.group_name,
                        created_at = EXCLUDED.created_at
                ''', (user_id, name, phone, group_name, datetime.now().isoformat()))
                conn.commit()
                logging.info(f"User {name} synced to remote for user_id {user_id}")
            except psycopg2.Error as e:
                logging.warning(f"Remote user sync failed: {e}")
            finally:
                conn.close()
        return success

    def add_transaction(self, user_id, savings, loans, income, expenses):
        """Add new transaction to local database, sync if online"""
        success = False
        try:
            with sqlite3.connect(self.local_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (user_id, savings, loans, income, expenses, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, savings, loans, income, expenses, datetime.now().isoformat()))
                conn.commit()
                logging.info(f"Transaction added locally for {user_id}")
                success = True
        except sqlite3.Error as e:
            logging.error(f"Local transaction add error: {e}")
            return False

        if self.is_online:
            try:
                conn = psycopg2.connect(self.db_url)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (user_id, savings, loans, income, expenses, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user_id, savings, loans, income, expenses, datetime.now().isoformat()))
                conn.commit()
                logging.info(f"Transaction synced to remote for {user_id}")
            except psycopg2.Error as e:
                logging.warning(f"Remote transaction sync failed: {e}")
            finally:
                conn.close()
        return success

    def get_user_history(self, user_id):
        """Get transaction history from local database"""
        try:
            with sqlite3.connect(self.local_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT savings, loans, income, expenses, timestamp
                    FROM transactions
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (user_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Local history fetch error for {user_id}: {e}")
            return []

    def simulate_wifi_sync(self):
        """Sync local unsynced transactions to remote database"""
        if not self.is_online:
            print("⚠️ No internet connection, sync skipped.")
            return
        print("\n🔄 Starting Wi-Fi sync simulation...")
        time.sleep(1)
        try:
            with sqlite3.connect(self.local_db) as local_conn:
                cursor = local_conn.cursor()
                cursor.execute('SELECT * FROM transactions WHERE synced = 0')
                unsynced = cursor.fetchall()
                if not unsynced:
                    print("✅ All data is already synced")
                    return
                print(f"📤 Found {len(unsynced)} unsynced transactions")

                conn = psycopg2.connect(self.db_url)
                remote_cursor = conn.cursor()
                for row in unsynced:
                    remote_cursor.execute('''
                        INSERT INTO transactions (user_id, savings, loans, income, expenses, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (row[1], row[2], row[3], row[4], row[5], row[6]))
                conn.commit()
                cursor.execute('UPDATE transactions SET synced = 1 WHERE synced = 0')
                local_conn.commit()
                print("✅ Sync completed successfully!")
                print(f"📊 {len(unsynced)} transactions uploaded to cloud")
                with open('sync_log.txt', 'a') as f:
                    f.write(f"{datetime.now().isoformat()}: Synced {len(unsynced)} transactions\n")
        except (sqlite3.Error, psycopg2.Error) as e:
            logging.error(f"Sync error: {e}")
        finally:
            conn.close()

    def get_memory_usage(self):
        """Get current memory usage for monitoring"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb

    def simulate_growth(self, savings, months, monthly_save):
        """Simulate future credit score based on savings growth"""
        new_savings = savings + (monthly_save * months)
        return max(0, min(100, 60 + (new_savings * 0.001)))

    def get_status_data(self):
        """Fetch status data from local database"""
        try:
            with sqlite3.connect(self.local_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM transactions')
                transaction_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM transactions WHERE synced = 0')
                unsynced_count = cursor.fetchone()[0]
                # Approximate local DB size (simplified)
                cursor.execute('SELECT pgsize_pretty(sum(length(data))) FROM (SELECT group_concat(name || value) as data FROM pragma_table_info(\'transactions\') UNION ALL SELECT group_concat(name || value) FROM pragma_table_info(\'users\'))')
                db_size = cursor.fetchone()[0] or 'N/A'
                return {
                    'user_count': user_count,
                    'transaction_count': transaction_count,
                    'unsynced_count': unsynced_count,
                    'db_size': db_size
                }
        except sqlite3.Error as e:
            logging.error(f"Local status data error: {e}")
            return {
                'user_count': 0,
                'transaction_count': 0,
                'unsynced_count': 0,
                'db_size': 'N/A'
            }

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
        if groweasy.add_user(user_id, name, phone, group_name):
            return render_template('success.html', message=f"User {name} added successfully!")
        else:
            return "❌ Error adding user. Check logs.", 500
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
    status_data = groweasy.get_status_data()
    memory_mb = groweasy.get_memory_usage()
    return render_template('status.html',
                           memory_mb=memory_mb,
                           user_count=status_data['user_count'],
                           transaction_count=status_data['transaction_count'],
                           unsynced_count=status_data['unsynced_count'],
                           db_size=status_data['db_size'])

@app.route('/status_data')
def status_data():
    groweasy = GrowEasy()
    return jsonify({'memory_mb': groweasy.get_memory_usage()})

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