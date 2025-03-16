from email_rag_system import EmailRAGSystem
import os

def main():
    # Initialize
    config_file = "config.yaml"  # Path to your configuration file
    email_rag_system = EmailRAGSystem(config_file)

    # Clear the cache (vault and embeddings)
    email_rag_system.clear_cache()

    # Define the query and date range
    # query = None  # Collect all emails
    # start_date = None
    # end_date = None

    # # Collect emails and regenerate vault and embeddings
    # success = email_rag_system.collect_emails(query=query, start_date=start_date, end_date=end_date)

    # if success:
    #     print("Emails collected and embeddings updated successfully.")
    # else:
    #     print("Failed to collect emails or update embeddings.")
    #     return

    # Now, query the RAG system.
    # user_query = "What is the current status of the project?"
    # print("Querying the RAG system with:", user_query)
    # response = email_rag_system.query_documents(user_query)
    # print("RAG System Response:", response)

if __name__ == "__main__":
    main()