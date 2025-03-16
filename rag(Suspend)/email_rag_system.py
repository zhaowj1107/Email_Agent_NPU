import os
import json
import base64
import re
from datetime import datetime
import argparse
import yaml
from bs4 import BeautifulSoup
import lxml
from dotenv import load_dotenv
import openai
from sentence_transformers import SentenceTransformer
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ANSI escape codes for colors
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'

class EmailRAGSystem:
    def __init__(self, config_file='config.yaml'):
        """
        Initialize the Email RAG System
        """
        self.config = self.load_config(config_file)
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        self.conversation_history = []
        self.setup_openai()
        
    def setup_openai(self):
        """
        Configure OpenAI settings
        """
        openai.api_base = self.config["api"]["base_url"]
        openai.api_key = self.config["api"]["api_key"]
        
    def load_config(self, config_file):
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Configuration file '{config_file}' not found.")
            exit(1)
            
    def clear_cache(self):
        """
        Clear the contents of the vault file and embeddings file.
        """
        if os.path.exists(self.config["vault_file"]):
            with open(self.config["vault_file"], "w", encoding="utf-8") as vault_file:
                vault_file.write("")
            print("Cleared existing vault file.")
        if os.path.exists(self.config["embeddings_file"]):
            with open(self.config["embeddings_file"], "w", encoding="utf-8") as embeddings_file:
                embeddings_file.write("")
            print("Cleared existing embeddings file.")

    # Email Collection Methods
    def collect_emails(self, query=None, start_date=None, end_date=None):
        """
        Collect emails using Gmail API and update embeddings.
        
        Args:
            query (str, optional): Search query for emails.
            start_date (str, optional): Start date in YYYY-MM-DD format.
            end_date (str, optional): End date in YYYY-MM-DD format.
        Returns:
            bool: True if successful, False otherwise.
        """
        print("Starting email collection...")
        service = self.get_gmail_service()
        if not service:
            return False

        try:
            # Build query string using provided parameters.
            query_parts = []
            if query:
                query_parts.append(query)
            if start_date:
                query_parts.append(f"after:{start_date}")
            if end_date:
                query_parts.append(f"before:{end_date}")
            query_string = " ".join(query_parts) if query_parts else ""
            print(f"Using search query: {query_string or 'No filters applied (collecting all emails)'}")

            # Removed maxResults parameter from the API call.
            results = service.users().messages().list(userId='me', q=query_string).execute()
            messages = results.get('messages', [])

            if not messages:
                print('No messages found.')
                return False

            print(f'Processing {len(messages)} messages...')
            all_chunks = []
            for message in messages:
                chunks = self.process_single_email(service, message['id'])
                if chunks:
                    all_chunks.extend(chunks)

            # Generate and save embeddings if there are new chunks.
            if all_chunks:
                new_embeddings = self.generate_embeddings(all_chunks)
                
                # Load existing embeddings.
                existing_embeddings = []
                if os.path.exists(self.config["embeddings_file"]):
                    with open(self.config["embeddings_file"], "r", encoding="utf-8") as file:
                        try:
                            existing_embeddings = json.load(file)
                        except json.JSONDecodeError:
                            print("Invalid JSON format in embeddings file. Starting fresh.")

                # Combine and save embeddings.
                combined_embeddings = existing_embeddings + new_embeddings
                self.save_embeddings(combined_embeddings)
                
                print("Email collection and embedding update completed.")
                return True

            return False

        except Exception as e:
            print(f"Error collecting emails: {e}")
            return False

    def get_gmail_service(self):
        """Get Gmail API service instance"""
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        creds = None

        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            print(f"Error creating Gmail service: {e}")
            return None

    def search_and_process_emails(self, service, query=None, start_date=None, end_date=None, max_emails=100):
        """
        Search and process emails using Gmail API, returning processed chunks.
        Parameters:
            query (str): Search query for emails (optional).
            start_date (str): Start date in 'YYYY-MM-DD' format (optional).
            end_date (str): End date in 'YYYY-MM-DD' format (optional).
            max_emails (int): Maximum number of emails to process.
        """
        query_parts = []
        if query:
            query_parts.append(query)
        if start_date:
            query_parts.append(f"after:{start_date}")
        if end_date:
            query_parts.append(f"before:{end_date}")
        
        query_string = " ".join(query_parts) if query_parts else ""
        print(f"Using search query: {query_string or 'No filters applied (collecting all emails)'}")

        results = service.users().messages().list(userId='me', q=query_string, maxResults=max_emails).execute()
        messages = results.get('messages', [])

        if not messages:
            print('No messages found.')
            return []

        print(f'Processing {len(messages)} messages...')
        all_chunks = []
        for message in messages:
            chunks = self.process_single_email(service, message['id'])
            if chunks:
                all_chunks.extend(chunks)

        return all_chunks

    def process_single_email(self, service, message_id):
        """
        Process a single email message and return its chunks.
        """
        try:
            msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
            metadata = self.extract_email_metadata(msg)
            content = self.get_email_content(service, msg)
            
            if content:
                chunks = self.chunk_text(content)
                self.save_chunks_to_vault(chunks, metadata)
                print(f"Processed email: {metadata['subject']}")
                return chunks
        except Exception as e:
            print(f"Error processing message {message_id}: {e}")
        return []

    # RAG Methods
    def query_documents(self, user_input):
        """
        Query the document collection using RAG
        """
        try:
            vault_content = self.load_vault_content()
            vault_embeddings = self.load_or_generate_embeddings(vault_content)
            
            response = self.deepseek_chat(
                user_input,
                self.config["system_message"],
                vault_embeddings,
                vault_content,
                self.config["model_name"],
                self.conversation_history,
                self.config["top_k"]
            )
            return response
        except Exception as e:
            print(f"Error querying documents: {e}")
            return "An error occurred while processing your request."

    def load_vault_content(self):
        """Load content from vault file"""
        if os.path.exists(self.config["vault_file"]):
            with open(self.config["vault_file"], "r", encoding='utf-8') as vault_file:
                return vault_file.readlines()
        return []

    def load_or_generate_embeddings(self, vault_content):
        """Load or generate embeddings for vault content"""
        if os.path.exists(self.config["embeddings_file"]):
            try:
                with open(self.config["embeddings_file"], "r", encoding="utf-8") as file:
                    embeddings = json.load(file)
                    return embeddings
            except json.JSONDecodeError:
                print(f"Invalid JSON format in embeddings file.")
                embeddings = []
        else:
            print(f"Generating new embeddings...")
            embeddings = self.generate_embeddings(vault_content)
            self.save_embeddings(embeddings)
            return embeddings

    def deepseek_chat(self, user_input, system_message, vault_embeddings, vault_content, model_name, conversation_history, top_k=3):
        """
        Process user input using DeepSeek chat model with RAG
        """
        # Generate embedding for the user query
        query_embedding = self.embedding_model.encode([user_input])[0]

        # Calculate similarities
        similarities = self.calculate_similarities(query_embedding, vault_embeddings)

        # Get top-k most relevant chunks
        top_k_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:top_k]
        relevant_chunks = [vault_content[i] for i in top_k_indices]

        # Prepare the chat context
        context = "\n\n".join(relevant_chunks)
        messages = [
            {"role": "system", "content": f"{system_message}\n\nContext from email archive:\n{context}"},
            *conversation_history,
            {"role": "user", "content": user_input}
        ]

        try:
            # Make API call to DeepSeek
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract the response
            answer = response.choices[0].message.content

            # Update conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": answer})

            return answer

        except Exception as e:
            print(f"Error in DeepSeek chat: {e}")
            return "I apologize, but I encountered an error while processing your request."

    def calculate_similarities(self, query_embedding, vault_embeddings):
        """
        Calculate cosine similarities between the query embedding and vault embeddings.
        """
        similarities = []
        for embedding in vault_embeddings:
            similarity = self.cosine_similarity(query_embedding, embedding)
            similarities.append(similarity)
        return similarities

    def cosine_similarity(self, vec1, vec2):
        """
        Calculate the cosine similarity between two vectors.
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(a * a for a in vec2) ** 0.5
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        return dot_product / (magnitude1 * magnitude2)

    def generate_embeddings(self, chunks):
        """
        Generate embeddings for a list of text chunks.
        """
        embeddings = []
        for chunk in chunks:
            embedding = self.embedding_model.encode([chunk])[0]
            embeddings.append(embedding.tolist())
        return embeddings

    def save_embeddings(self, embeddings):
        """Save embeddings to file"""
        with open(self.config["embeddings_file"], "w", encoding="utf-8") as file:
            json.dump(embeddings, file)

    # Shared Utility Methods
    def clean_email_text(self, text):
        """Clean email text"""
        patterns = [
            (r'(?m)^-{3,}.*?Forwarded message.*?-{3,}\s*$', ''),
            (r'(?m)^(From|To|Sent|Date|Subject|Cc|Bcc):.*?\n', ''),
            (r'(?m)^--\s*\n.*?(?=\n\n|\Z)', ''),
            (r'(?m)^Regards,?\s*.*?(?=\n\n|\Z)', ''),
            (r'(?m)^Best,?\s*.*?(?=\n\n|\Z)', ''),
            (r'(?m)^CONFIDENTIAL.*?(?=\n\n|\Z)', '', re.IGNORECASE),
            (r'(?m)^Disclaimer:.*?(?=\n\n|\Z)', '', re.IGNORECASE),
            (r'(?m)^>+.*$', ''),
            (r'(?m)^On.*wrote:$', ''),
            (r'\n\s*\n\s*\n+', '\n\n'),
            (r'\s+', ' ')
        ]
        
        for pattern in patterns:
            if len(pattern) == 2:
                text = re.sub(pattern[0], pattern[1], text)
            else:
                text = re.sub(pattern[0], pattern[1], text, flags=pattern[2])
        
        return text.strip()

    def extract_email_metadata(self, msg):
        """Extract metadata from email message"""
        headers = msg['payload']['headers']
        metadata = {
            'subject': '',
            'from': '',
            'to': '',
            'date': ''
        }
        
        for header in headers:
            name = header['name'].lower()
            if name in metadata:
                metadata[name] = header['value']
        
        return metadata

    def get_email_content(self, service, msg):
        """Extract and decode email content"""
        if 'payload' not in msg:
            return None

        parts = [msg['payload']]
        content = []

        while parts:
            part = parts.pop()
            
            if 'parts' in part:
                parts.extend(part['parts'])
            
            if 'body' in part and 'data' in part['body']:
                try:
                    data = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    if part.get('mimeType') == 'text/html':
                        soup = BeautifulSoup(data, 'lxml')
                        content.append(soup.get_text())
                    else:
                        content.append(data)
                except Exception as e:
                    print(f"Error decoding email content: {e}")
                    continue

        return '\n'.join(content) if content else None

    def save_chunks_to_vault(self, chunks, metadata):
        """Save processed chunks to the vault file"""
        if not chunks:
            return

        with open(self.config["vault_file"], "a", encoding='utf-8') as vault_file:
            for chunk in chunks:
                # Add metadata as context
                chunk_with_metadata = f"Subject: {metadata['subject']}\nFrom: {metadata['from']}\nDate: {metadata['date']}\n\n{chunk}\n\n---\n"
                vault_file.write(chunk_with_metadata)

    def chunk_text(self, text, max_length=1000):
        """Chunk text into smaller pieces"""
        text = self.clean_email_text(text)
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(paragraph) > max_length:
                sentences = re.split(r'(?<=[.!?]) +', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 < max_length:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
            else:
                if len(current_chunk) + len(paragraph) + 2 < max_length:
                    current_chunk += paragraph + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

def main():
    parser = argparse.ArgumentParser(description="Email RAG System")
    parser.add_argument("--mode", choices=['collect', 'query'], required=True,
                      help="Mode of operation: 'collect' emails or 'query' documents")
    parser.add_argument("--config", default="config.yaml",
                      help="Path to configuration file")
    parser.add_argument("--query", help="Search query for emails or question for documents")
    parser.add_argument("--startdate", help="Start date (YYYY/MM/DD)")
    parser.add_argument("--enddate", help="End date (YYYY/MM/DD)")
    
    args = parser.parse_args()
    
    # Initialize the system
    system = EmailRAGSystem(args.config)
    
    if args.mode == 'collect':
        # Convert dates if provided
        start_date = None
        end_date = None
        if args.startdate:
            start_date = datetime.strptime(args.startdate, "%Y/%m/%d").strftime("%Y/%m/%d")
        if args.enddate:
            end_date = datetime.strptime(args.enddate, "%Y/%m/%d").strftime("%Y/%m/%d")
            
        # Collect emails
        system.collect_emails(args.query, start_date, end_date)
        
    elif args.mode == 'query':
        if not args.query:
            # Interactive mode
            while True:
                user_input = input(YELLOW + "Ask a question (or type 'quit' to exit): " + RESET_COLOR)
                if user_input.lower() == 'quit':
                    break
                response = system.query_documents(user_input)
                print(NEON_GREEN + "Response:\n\n" + response + RESET_COLOR)
        else:
            # Single query mode
            response = system.query_documents(args.query)
            print(NEON_GREEN + "Response:\n\n" + response + RESET_COLOR)