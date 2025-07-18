# GrowEasy_Web

## Overview
A microfinance application to manage user savings, loans, and credit assessments.

## Live Demo
- [Deployed App](https://groweasy-web.onrender.com)

## Installation
1. Clone the repository: `git clone https://github.com/yourusername/groweasy_web.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variable: `set DATABASE_URL=postgresql://groweasy_web_user:DgIu3tONEj7gN7QAyQDPLUo1KkwPpkY8@dpg-d1rvoa6r433s73b875g0-a.oregon-postgres.render.com/groweasy_web`
4. Run the app: `python main.py`

## Usage
- Access via browser at `/` for the menu.
- Add users at `/add_user`.
- Assess credit at `/credit_assessment`.
- View history at `/view_history`.
- Sync data at `/sync`.
- Check status at `/status`.
- Simulate growth at `/simulate`.

## Backup Instructions
- Run `.\backup.bat` to create `backup.sql` using the external database URL.

## Requirements
- Python 3.x
- Flask
- psycopg2
- psutil
- PostgreSQL client tools (for backup)

## License
MIT License