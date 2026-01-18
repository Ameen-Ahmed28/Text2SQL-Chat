from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import streamlit as st
from urllib.parse import quote_plus
import sqlglot
from sqlglot import exp
from sqlalchemy import text
import os
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")
import pandas as pd


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

def get_sql_chain(db):
  
  def execute_sql(sql: str):
    with db._engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        columns = result.keys()
        return {
            "rows": rows,
            "columns": columns
        }
    

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
  
  # llm = ChatOpenAI(model="gpt-4-0125-preview")
  llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
  parser = StrOutputParser()
  sql_chain = prompt | llm | parser | RunnableLambda(validate_sql) | RunnableLambda(execute_sql) 
  return sql_chain


    
def get_response(user_query: str, db: SQLDatabase, chat_history: list):
  sql_chain = get_sql_chain(db)
  
  return sql_chain.invoke({
    "question": user_query,
    "chat_history": chat_history,
    "schema" : db.get_table_info()
  })
    
  
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
      AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
    ]


st.set_page_config(page_title="Chat with MySQL", page_icon=":speech_balloon:")

st.title("Chat with MySQL")

with st.sidebar:
    st.subheader("Settings")
    st.write("This is a simple chat application using MySQL. Connect to the database and start chatting.")
    
    st.text_input("Host", value=DB_HOST, key="Host")
    st.text_input("Port", value=DB_PORT, key="Port")
    st.text_input("User", value=DB_USER, key="User")
    st.text_input("Password", type="password", value=DB_PASSWORD, key="Password")
    st.text_input("Database", value=DB_NAME, key="Database")
    
    if st.button("Connect"):
        with st.spinner("Connecting to database..."):
            db = init_db(
                st.session_state["User"],
                st.session_state["Password"],
                st.session_state["Host"],
                st.session_state["Port"],
                st.session_state["Database"]
            )
            st.session_state.db = db
            st.success("Connected to database!")
    
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

user_query = st.chat_input("Type a message...")
if user_query is not None and user_query.strip() != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    
    with st.chat_message("Human"):
        st.markdown(user_query)
        
    with st.chat_message("AI"):
        response = get_response(user_query, st.session_state.db, st.session_state.chat_history)
        if isinstance(response, dict) and "rows" in response:
            df = pd.DataFrame(response["rows"], columns=response["columns"])
            st.dataframe(df, use_container_width=True)
        else:
            st.markdown(str(response))
        
    st.session_state.chat_history.append(AIMessage(content=str(response)))