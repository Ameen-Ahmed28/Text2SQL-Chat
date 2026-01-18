🧠 Chat with MySQL using LLM (Text-to-SQL)

A production-grade Text-to-SQL application built using LangChain LCEL, Groq LLM, SQLGlot validation, SQLAlchemy 2.0, and Streamlit.

Users can ask natural-language questions and safely query a MySQL database with read-only SQL execution, dynamic table rendering, and conversational memory.

✨ Features

✅ Natural language → SQL

✅ SQL AST validation using sqlglot

✅ Read-only enforcement (SELECT only)

✅ Automatic LIMIT protection

✅ Dynamic schema injection

✅ SQLAlchemy 2.0 compliant execution

✅ Dynamic table rendering (no hardcoded columns)

✅ Streamlit chat UI

✅ Environment-based DB configuration

✅ Conversation memory

✅ Safe execution pipeline

🧱 Architecture
User Question
      ↓
LLM (Groq - LLaMA 3.3)
      ↓
SQL Generation
      ↓
SQLGlot AST Validation
      ↓
Read-only Enforcement
      ↓
SQLAlchemy text() Execution
      ↓
Rows + Column Metadata
      ↓
Dynamic Streamlit Table

🛠 Tech Stack
Component	Tool
LLM	Groq (LLaMA 3.3 70B)
Framework	LangChain (LCEL)
SQL Validation	SQLGlot
Database	MySQL
ORM	SQLAlchemy 2.0
Driver	PyMySQL
UI	Streamlit
Config	python-dotenv
📂 Project Structure
.
├── app.py
├── .env
├── requirements.txt
└── README.md

⚙️ Installation
1️⃣ Clone the repository
git clone https://github.com/your-username/chat-with-mysql-llm.git
cd chat-with-mysql-llm

2️⃣ Create virtual environment (uv recommended)
uv venv

3️⃣ Install dependencies
uv pip install -r requirements.txt

4️⃣ Configure environment variables

Create a .env file:

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database

GROQ_API_KEY=your_groq_api_key


⚠️ Never commit .env to GitHub

Add to .gitignore:

.env

▶️ Run the app
uv run streamlit run app.py


Then open:

http://localhost:8501

💬 Example Questions

“Show top 5 customers by credit limit”

“List all employees in the sales department”

“Total number of orders per customer”

“Which products were never ordered?”

“Top 10 customers by revenue”

🔐 SQL Safety Rules

The system enforces:

❌ INSERT

❌ UPDATE

❌ DELETE

❌ DROP

❌ ALTER

❌ CREATE

Only:

SELECT


is allowed.

If no LIMIT is provided, it automatically adds:

LIMIT 100

🧠 Why SQLGlot?

SQLGlot parses SQL into an AST (Abstract Syntax Tree) allowing:

Structural validation

Clause inspection

Write-operation blocking

Safe execution of LLM-generated SQL

This is far safer than regex-based validation.

📊 Output Handling

If query returns tabular data → rendered as DataFrame

If query returns message → shown as text

Columns detected dynamically (no hardcoding)

🔍 Example Output
customerNumber	  customerName	       creditLimit
125	            Havel & Zbyszek Co	      0.00
168	            American Souvenirs Inc	  0.00
169	            Porto Imports Co	        0.00
