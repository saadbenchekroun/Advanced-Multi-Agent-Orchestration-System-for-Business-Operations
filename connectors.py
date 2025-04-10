import requests
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_system")

class CRMConnector:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def connect(self):
        try:
            # Example: Fetching contacts from the CRM
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get(f'{self.base_url}/contacts', headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Connected to CRM at {self.base_url}. Fetched contacts successfully.")
                return response.json()
            else:
                logger.error(f"Failed to connect to CRM. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to CRM: {e}")

    def create_contact(self, contact_data):
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.post(f'{self.base_url}/contacts', headers=headers, data=json.dumps(contact_data))
            
            if response.status_code == 201:
                logger.info(f"Created contact in CRM successfully.")
                return response.json()
            else:
                logger.error(f"Failed to create contact. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error creating contact: {e}")

class GoogleAnalyticsConnector:
    def __init__(self, api_key, view_id):
        self.api_key = api_key
        self.view_id = view_id

    def track_event(self, event_category, event_action, event_label):
        try:
            # Note: Google Analytics typically uses the Measurement Protocol for tracking events.
            # This example simplifies the process but you should use the official library or API for production.
            data = {
                'v': '1',
                'tid': self.api_key,
                'cid': '555',  # Client ID
                't': 'event',
                'ec': event_category,
                'ea': event_action,
                'el': event_label
            }
            response = requests.post('https://www.google-analytics.com/collect', data=data)
            
            if response.status_code == 200:
                logger.info(f"Tracked event in Google Analytics view {self.view_id} successfully.")
            else:
                logger.error(f"Failed to track event. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error tracking event: {e}")

class JiraConnector:
    def __init__(self, api_key, base_url, project_keys):
        self.api_key = api_key
        self.base_url = base_url
        self.project_keys = project_keys

    def create_issue(self, project_key, summary, description):
        try:
            auth = (self.api_key, 'x')  # Jira uses basic auth with 'x' as the password placeholder
            headers = {
                'Content-Type': 'application/json'
            }
            data = {
                'fields': {
                    'project': {
                        'key': project_key
                    },
                    'summary': summary,
                    'description': description,
                    'issuetype': {
                        'name': 'Task'
                    }
                }
            }
            response = requests.post(f'{self.base_url}/rest/api/2/issue', auth=auth, headers=headers, data=json.dumps(data))
            
            if response.status_code == 201:
                logger.info(f"Created issue in Jira project {project_key} successfully.")
                return response.json()
            else:
                logger.error(f"Failed to create issue. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error creating issue: {e}")

class QuickBooksConnector:
    def __init__(self, api_key, company_id):
        self.api_key = api_key
        self.company_id = company_id

    def create_invoice(self, customer_id, amount):
        try:
 # Note: QuickBooks API requires OAuth2 authentication and specific headers.
            # For simplicity, this example uses a placeholder for authentication.
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'CustomerRef': {
                    'value': customer_id
                },
                'TotalAmt': amount
            }
            response = requests.post(f'https://quickbooks.api.intuit.com/v3/company/{self.company_id}/invoice', headers=headers, data=json.dumps(data))
            
            if response.status_code == 201:
                logger.info(f"Created invoice in QuickBooks company {self.company_id} successfully.")
                return response.json()
            else:
                logger.error(f"Failed to create invoice. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")

class FigmaConnector:
    def __init__(self, api_key, project_ids):
        self.api_key = api_key
        self.project_ids = project_ids

    def get_project(self, project_id):
        try:
            headers = {
                'X-Figma-Token': self.api_key
            }
            response = requests.get(f'https://api.figma.com/v1/files/{project_id}', headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Fetched Figma project {project_id} successfully.")
                return response.json()
            else:
                logger.error(f"Failed to fetch project. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching project: {e}")

class GitHubConnector:
    def __init__(self, api_key, repositories):
        self.api_key = api_key
        self.repositories = repositories

    def create_issue(self, repository, title, body):
        try:
            headers = {
                'Authorization': f'token {self.api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'title': title,
                'body': body
            }
            response = requests.post(f'https://api.github.com/repos/{repository}/issues', headers=headers, data=json.dumps(data))
            
            if response.status_code == 201:
                logger.info(f"Created issue in GitHub repository {repository} successfully.")
                return response.json()
            else:
                logger.error(f"Failed to create issue. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error creating issue: {e}")

class SlackConnector:
    def __init__(self, api_key, channels):
        self.api_key = api_key
        self.channels = channels

    def send_message(self, channel, message):
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'channel': channel,
                'text': message
            }
            response = requests.post('https://slack.com/api/chat.postMessage', headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                logger.info(f"Sent message to Slack channel {channel} successfully.")
                return response.json()
            else:
                logger.error(f"Failed to send message. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")