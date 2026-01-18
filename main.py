from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage
from dotenv import load_dotenv
import os
import sqlglot
from sqlglot import exp
from urllib.parse import quote_plus
load_dotenv()

def init_db(user, password, host, port, database):
    password = quote_plus(password)
    db_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)


def validate_sql(sql: str):
    try:
        expression = sqlglot.parse_one(sql)

        # ✅ must be SELECT
        if not isinstance(expression, exp.Select):
            raise ValueError("Only SELECT queries are allowed")

        # ❌ disallowed clauses
        forbidden = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Alter,

            exp.Create,
        )

        for node in expression.walk():
            if isinstance(node, forbidden):
                raise ValueError("Write operations are not allowed")

        # ✅ enforce LIMIT for safety
        if expression.args.get("limit") is None:
            expression = expression.limit(100)

        return expression.sql()

    except Exception as e:
        raise ValueError(f"Invalid SQL: {e}")
    

host = "localhost"
port = 3306
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")
db = init_db(user, password, host, port, database)
print("DB is connected...")
user_query = "Retrieve 5 customer number, customer name,  credit limit of customers order it from low to high on credit limit and customer number"
chat_history = []
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
parser = StrOutputParser()
schema = db.get_table_info()
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert SQL generator.

Rules:
- Generate ONLY a valid SQL query.
- DO NOT include explanations.
- DO NOT include markdown.
- DO NOT include comments.
- DO NOT include natural language.
- The query MUST be read-only (SELECT only).
- Use only the tables and columns provided in the schema.
- If the question cannot be answered using the schema, return:
  SELECT 'INSUFFICIENT_DATA';

Always follow SQL syntax strictly.
"""
    ),

    # conversation memory
    MessagesPlaceholder(variable_name="chat_history"),

    (
        "human",
        """
Database schema:
{schema}

Question:
{question}
"""
    ),
])

sql_chain = prompt | llm | parser | RunnableLambda(validate_sql) | RunnableLambda(lambda sql : db.run(sql)) 
response = sql_chain.invoke({
    "question" : user_query,
    "schema" : schema,
    "chat_history" : chat_history
})
chat_history.append(AIMessage(content=str(response)))
print(response)