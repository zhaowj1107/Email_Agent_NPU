import os
import sys
import flask as fl

module_path = os.path.abspath("email_agent")
sys.path.append(module_path)
import gmail_monitor as gm

module_path = os.path.abspath("email_action")
sys.path.append(module_path)
import gmail_categorization as gc
import gmail_api as ga
from datetime import datetime
# import google_calendar.calendar_api as gc

def main():
    email_id = None
    while True:
        email, email_id = gm.monitor_email(email_id)
        print(email)
        print("")
        # print(email_id)

        custom_prompt = """
        Analyze this email and categorize it:
        A: Archive (low priority)
        B: Reply (medium priority)
        M: Meeting/Important (high priority)
        
        Return only a single letter.
        """
        print("Categoring email...\n")
        category_custom = gc.categorize_email(email, custom_prompt)
        print(f"Category with custom prompt: {category_custom}")

def web_demo():
    app = fl.Flask(__name__)
    
    # Store processed emails to display in the web interface
    emails_processed = []
    
    @app.route('/')
    def index():
        return fl.render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Monitor Dashboard</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .email-card { 
                    border: 1px solid #ddd; 
                    margin-bottom: 15px; 
                    padding: 15px; 
                    border-radius: 5px;
                }
                .category-A { border-left: 5px solid gray; }
                .category-B { border-left: 5px solid orange; }
                .category-M { border-left: 5px solid red; }
                .timestamp { color: #777; font-size: 0.8em; }
                .refresh-btn { 
                    padding: 10px; 
                    background-color: #4285F4; 
                    color: white; 
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <h1>Email Monitor Dashboard</h1>
            <p>This page automatically refreshes every 30 seconds. <button class="refresh-btn" onclick="location.reload()">Refresh Now</button></p>
            
            <h2>Processed Emails</h2>
            {% if emails %}
                {% for email in emails %}
                <div class="email-card category-{{ email.category }}">
                    <h3>{{ email.subject }}</h3>
                    <p><strong>From:</strong> {{ email.sender }}</p>
                    <p><strong>Category:</strong> 
                        {% if email.category == 'A' %}
                            Archive (Low Priority)
                        {% elif email.category == 'B' %}
                            Reply (Medium Priority)
                        {% elif email.category == 'M' %}
                            Meeting/Important (High Priority)
                        {% endif %}
                    </p>
                    <p>{{ email.body|truncate(200) }}</p>
                    <p class="timestamp">Processed at: {{ email.timestamp }}</p>
                </div>
                {% endfor %}
            {% else %}
                <p>No emails processed yet. Waiting for new emails...</p>
            {% endif %}
        </body>
        </html>
        """, emails=emails_processed)
    
    @app.route('/process-emails', methods=['GET'])
    def process_emails():
        global emails_processed
        
        email_id = None
        # Process a single email
        email, email_id = gm.monitor_email(email_id)
        
        if email:
            custom_prompt = """
            Analyze this email and categorize it:
            A: Archive (low priority)
            B: Reply (medium priority)
            M: Meeting/Important (high priority)
            
            Return only a single letter.
            """
            category = gc.categorize_email(email, custom_prompt)
            
            # Extract relevant information
            email_info = {
                'subject': email.get('subject', 'No Subject'),
                'sender': email.get('from', 'Unknown Sender'),
                'body': email.get('body', 'No Content'),
                'category': category,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add to processed emails list (keep most recent 10)
            emails_processed.insert(0, email_info)
            emails_processed = emails_processed[:10]
            
            return fl.jsonify({"status": "success", "email": email_info})
        return fl.jsonify({"status": "no new emails"})
    
    # Run the Flask app
    app.run(debug=True, port=5000)


        # Replace main() call with web_demo()
if __name__ == "__main__":
    web_demo()

        # if category_custom == "A":
        #     ga.archive_emails(email)
        # elif category_custom == "B":
        #     ga.reply_email(email)
        #     gc.if_calendar(email)
        # elif category_custom == "M":
        #     ga.simple_draft(email)
        #     gc.if_calendar(email)
