# app/main.py

from database.mongo_client import get_db
from agents.router_agent import run_pipeline

def main():
    db = get_db()

    print("🧠 Natural Language → MongoDB System")
    print("Type 'exit' to quit\n")

    while True:
        user_query = input("Ask your query: ")

        if user_query.lower() == "exit":
            break

        response = run_pipeline(db, user_query)

        if "error" in response:
            print("❌", response["error"])
        else:
            print("\n🔹 Generated Query:")
            print(response["query"])

            print("\n🔹 Explanation:")
            print(response["explanation"])

            print("\n🔹 Result:")
            print(response["result"])
            print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()