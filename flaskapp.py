import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from langchain_chroma import Chroma
import re

from get_embedding_function import get_embedding_function

CHROMA_PATH = "C:\\Users\\faa44\\OneDrive\\Desktop\\testing3\\chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

class QueryThread(QThread):
    response_ready = pyqtSignal(str)

    def __init__(self, query_text):
        super().__init__()
        self.query_text = query_text

    def run(self):
        response_text = self.query_rag(self.query_text)
        self.response_ready.emit(response_text)

    def query_rag(self, query_text):
        if query_text.lower() in ['hi', 'hello', 'hey']:
            return "Hello! How can I assist you today?\n I'm AI Assistant tool to answer questions, resolve errors and provide user manuals for SAP"
        elif query_text.lower() in ['how are you?', 'how are u?', 'how are you', 'how are u']:
            return "I'm doing well! How about you?"

        embedding_function = get_embedding_function()
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

        results = db.similarity_search_with_score(query_text, k=2)

        if not results:
            return "Sorry, I don't understand your question. Please try asking something else."

        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

        urls = self.extract_urls(context_text)

        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=query_text)

        model = Ollama(model="mistral")
        response_text = model.invoke(prompt)

        sources = [doc.metadata.get("id", None) for doc, _score in results]
        formatted_response = f"{response_text}\n\nSources:\n" + "\n".join(f"- {source}" for source in sources)

        if urls:
            formatted_response += "\n\nHere are some relevant links from the documents:\n" + "\n".join(urls)

        return formatted_response

    def extract_urls(self, text):
        url_pattern = r'(https?://[^\s]+)'
        return re.findall(url_pattern, text)

class AIChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant Tool")
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Header
        self.header = QLabel("<b>Welcome to SAP AI Assistant Tool</b>")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFixedHeight(50)
        self.header.setStyleSheet(""" 
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #330867, stop:1 #30cfd0);
            color: white;
            font-size: 24px;
            padding: 10px;
        """)
        layout.addWidget(self.header)

        # Chat container setup
        self.chat_container = QScrollArea()
        self.chat_widget = QWidget()  # Create a widget to hold messages
        self.chat_layout = QVBoxLayout(self.chat_widget)  # Use a vertical layout for messages
        self.chat_container.setWidget(self.chat_widget)
        self.chat_container.setWidgetResizable(True)
        self.chat_container.setStyleSheet("background-color: #f4f4f4; padding: 10px;")
        layout.addWidget(self.chat_container)

        # Input layout
        input_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask something...")
        input_layout.addWidget(self.input_box)

        # Send button (with icon)
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon("send.png"))
        self.send_button.setIconSize(QSize(40, 40))  # Adjust icon size here
        self.send_button.clicked.connect(self.send_query)
        self.send_button.setStyleSheet("border: none;")
        input_layout.addWidget(self.send_button)

        # Clear button (with icon)
        # self.clear_button = QPushButton()
        # self.clear_button.setIcon(QIcon("clear.png"))
        # self.clear_button.setIconSize(QSize(20, 40))  # Adjust icon size here
        # self.clear_button.clicked.connect(self.clear_chat)
        # self.clear_button.setStyleSheet("border: none;")
        # input_layout.addWidget(self.clear_button)

        layout.addLayout(input_layout)
        self.setLayout(layout)

    def append_message(self, text, msg_type):
        # Set up a horizontal layout for messages
        message_layout = QHBoxLayout()
        
        # Add user/bot icon
        icon_label = QLabel()
        if msg_type == "user":
            icon_label.setPixmap(QPixmap("user_logo.png"))  # Replace with your user logo path
            bg_color = "#d3eafd"  # Light blue for user message
        else:
            icon_label.setPixmap(QPixmap("bot_logo.png"))  # Replace with your bot logo path
            bg_color = "#d0f0c0"  # Light green for bot message

        icon_label.setFixedSize(80, 80)
        icon_label.setScaledContents(True)

        # Create message label
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"background-color: {bg_color}; padding: 8px; border-radius: 8px;")
        message_label.setFrameStyle(QFrame.Box)
        message_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)  # Adjust size policy

        # Align messages and icons
        if msg_type == "user":
            message_layout.addWidget(icon_label)
            message_layout.addWidget(message_label, 1)
        else:
            message_layout.addWidget(message_label, 1)
            message_layout.addWidget(icon_label)

        # Add the message layout to the chat widget's layout
        self.chat_layout.addLayout(message_layout)

        # Scroll to the bottom
        self.chat_container.verticalScrollBar().setValue(self.chat_container.verticalScrollBar().maximum())

    def send_query(self):
        query_text = self.input_box.text()
        if query_text:
            self.append_message(query_text, "user")
            self.input_box.clear()

            # Start the background thread for bot response
            self.thread = QueryThread(query_text)
            self.thread.response_ready.connect(self.handle_bot_response)
            self.thread.start()

    def handle_bot_response(self, response_text):
        self.append_message(response_text, "bot")

    def clear_chat(self):
        self.chat_layout = QVBoxLayout(self.chat_widget)  # Reset the layout to clear messages
        self.chat_widget.setLayout(self.chat_layout)  # Reassign the layout
        self.chat_container.verticalScrollBar().setValue(self.chat_container.verticalScrollBar().maximum())  # Reset scroll bar

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ai_chat_app = AIChatApp()
    ai_chat_app.show()
    sys.exit(app.exec_())
