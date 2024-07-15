from langflow.base.io.chat import ChatComponent
from langflow.inputs import BoolInput
from langflow.io import DropdownInput, MessageTextInput, Output
from langflow.memory import store_message
from langflow.schema.message import Message
import smtplib
import re
from email.message import EmailMessage


class ChatOutput(ChatComponent):
    display_name = "Chat Output With Gmail"
    description = "Display a chat message in the Playground."
    icon = "ChatOutput"
    name = "ChatOutput"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Text",
            info="Message to be passed as output.",
        ),
        BoolInput(
            name="store_message",
            display_name="Store Messages",
            info="Store the message in the history.",
            value=True,
            advanced=True,
        ),
        DropdownInput(
            name="sender",
            display_name="Sender Type",
            options=["Machine", "User"],
            value="Machine",
            advanced=True,
            info="Type of sender.",
        ),
        MessageTextInput(
            name="sender_name", display_name="Sender Name", info="Name of the sender.", value="AI", advanced=True
        ),
        MessageTextInput(
            name="session_id", display_name="Session ID", info="Session ID for the message.", advanced=True
        ),
        MessageTextInput(
            name="data_template",
            display_name="Data Template",
            value="{text}",
            advanced=True,
            info="Template to convert Data to Text. If left empty, it will be dynamically set to the Data's text key.",
        ),
        MessageTextInput(
            name="sender_gmail", display_name="Sender Gmail", info="Gmail of the sender."
        ),
        MessageTextInput(
            name="sender_gmail_app_password", display_name="Sender Gmail App Password", info="Gmail app password for auth."
        ),
    ]
    outputs = [
        Output(display_name="Message", name="message", method="message_response"),
    ]
    
    def send_email(self, sender_email, recipient_email, email_content):
        if self.sender_gmail and self.sender_gmail_app_password:
            msg = EmailMessage()
            msg.set_content(email_content)
            msg['Subject'] = f"Neuroflow - Report"
            msg['From'] = sender_email
            msg['To'] = recipient_email
            
            # Send the message via localhost SMTP server.
            s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            s.ehlo()
            s.login(self.sender_gmail, self.sender_gmail_app_password)
            s.send_message(msg)
            s.quit()
        return
        
    def parse_report(self) -> dict:
        # Regular expression pattern for matching email addresses
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # ---Report Title---
        # This is the content of the report that we want to extract.
        # It can span multiple lines.
        # 4. **Email Address
        
        content_pattern = r'---Report Title---(.*?)4\. \*\*Email Address'
        
        match = re.search(content_pattern, self.input_value, re.DOTALL)
        emails = re.findall(email_pattern, self.input_value)
        
        parsed_report = {
            'recipient_email': emails[0] if emails else "ichwanharyosembodo96@gmail.com",
            'email_content': match.group(1).strip() if match else "No report generated!"
        }

        return parsed_report
        

    def message_response(self) -> Message:
        message = Message(
            text=self.input_value,
            sender=self.sender,
            sender_name=self.sender_name,
            session_id=self.session_id,
        )
        if self.session_id and isinstance(message, Message) and isinstance(message.text, str):
            store_message(
                message,
                flow_id=self.graph.flow_id,
            )
            self.message.value = message
            
        if "Report Title" in self.input_value and "End of Report" in self.input_value:
            reports = self.parse_report()
            self.send_email("ichwan@neuroflow.co", reports['recipient_email'], reports['email_content'])

        self.status = message
        return message
