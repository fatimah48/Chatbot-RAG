from flask import Flask, request, jsonify, render_template_string
from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
import re

from get_embedding_function import get_embedding_function

CHROMA_PATH = "C:\\Users\\faa44\\OneDrive\\Desktop\\testing3\\chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query_text = request.form['query_text']
        response_text = query_rag(query_text)
        return jsonify({"response": response_text})
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>AI Assistant Tool</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                header { 
                    background: linear-gradient(to right, #30cfd0, #330867);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 24px;
                }
                .chat-container { max-width: 600px; margin: 20px auto; }
                .chat-box { border: 1px solid #ccc; padding: 10px; height: 400px; overflow-y: auto; background-color: #f4f4f4; white-space: pre-wrap; }
                .message { margin: 10px 0; padding: 10px; border-radius: 10px; display: flex; align-items: center;max-width: 100%;  }
                .user { background-color: #d1e7dd;}
                .bot { background-color: #cce5ff; color: #004085; max-width: 100%; }
                .message img { width: 30px; height: 30px; margin-right: 10px; border-radius: 50%;max-width: 100%; }
                .input-box { display: flex; margin-top: 10px; }
                .input-box input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 5px 0 0 5px; }
                .input-box button { padding: 10px; border: 1px solid #ccc; border-left: none; background-color: #007bff; color: white; border-radius: 0 5px 5px 0; cursor: pointer; }
                .input-box button:hover { background-color: #0056b3; }
                .source-list { margin-top: 20px; padding-left: 20px; margin-bottom: 20px; }
                .card-container {
                    display: flex;
                    justify-content: space-evenly;
                    position: fixed;
                    bottom: 20px;
                    width: 100%;
                    left: 0;
                    overflow: hidden;
                    padding: 0 10px;
                }
                .promotion-text {
                    text-align: center;
                    font-size: 20px;
                    color: #800080; /* Dark purple */
                    position: relative;
                    top: 60px; /* Adjust this value to move the text down */
                    font-weight: bold;
                }
                        
                .card {
                    background-color: #bbe4e9;
                    border-radius: 10px;
                    padding: 10px 20px;
                    margin: 5px;
                    font-size: 14px;
                    # opacity: 0.4;
                    color: #333;
                    font-weight: bold;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    transition: opacity 0.3s ease, transform 0.3s ease, background-color 0.3s ease;
                }
           
                .card.active{
                    opacity:1;
                    transform:scale(1.05); 
                    background-color: #b39ddb;        
                                  }
                                  

                .card:hover {
                    transform: scale(1.05);
                   
                }
                
              
                                  
           

               

            </style>
        </head>
        <body>
            <div style="position: absolute; top: 20px; left: 20px; display: flex; align-items: center;">
                <img src="https://img.icons8.com/?size=100&id=wsixpbozZFBy&format=png&color=000000" alt="icon" style="width:30px; height:30px; vertical-align: middle;">
                <span style="font-size: 14px; margin-left: 10px;color: white;">Retrieval Augmented Generation</span>
            </div>

            <header>
                <b>Welcome to AI Assistant Tool</b>

            </header>
            <div class="chat-container">
                <div class="chat-box" id="chat-box"></div>
                <div class="input-box">
                    <input type="text" id="query_text" placeholder="Ask something...">
                    <button onclick="sendQuery()">
                        <img src="https://img.icons8.com/ios-filled/50/ffffff/send.png" alt="Send" style="width: 20px; height: 20px;">
                    </button>
                    <button id="clear-button">
                         <img src="https://img.icons8.com/?size=100&id=47576&format=png&color=000000" alt="Clear" style="width:20px; height:20px;">
                    </button>

                </div>
            </div>
            <script>
                function appendMessage(text, type) {
                    const chatBox = document.getElementById('chat-box');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message ' + type;

                    const img = document.createElement('img');
                    if (type === 'user') {
                        img.src = 'https://img.icons8.com/?size=100&id=kDoeg22e5jUY&format=png&color=000000'; // User image
                    } else {
                        img.src = 'https://img.icons8.com/?size=100&id=XiSP6YsZ9SZ0&format=png&color=000000'; // Bot image
                    }

                    messageDiv.appendChild(img);
                    const textNode = document.createTextNode(text);
                    messageDiv.appendChild(textNode);
                    
                    chatBox.appendChild(messageDiv);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
                
                function sendQuery() {
                    const queryText = document.getElementById('query_text').value;
                    appendMessage(queryText, 'user');
                    
                    fetch('/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: new URLSearchParams({ 'query_text': queryText })
                    })
                    .then(response => response.json())
                    .then(data => {
                        appendMessage(data.response, 'bot');
                        document.getElementById('query_text').value = ''; // Clear input field after sending
                    });
                }
                document.getElementById("clear-button").addEventListener("click", function() {
                    document.querySelector(".chat-box").innerHTML = "";
                });
                document.addEventListener("DOMContentLoaded", function() {
                        const cards = document.querySelectorAll(".card");
                        let currentCard = 0;
                        function showCard(n) {

                            cards.forEach(card => card.classList.remove('active'));
                            cards[n].classList.add('active');

                        }

                        function nextCard() {

                            currentCard = (currentCard + 1) % cards.length;
                            showCard(currentCard);

                        }
                        // Show the first card initially
                        showCard(currentCard);
                        // Automatically move to the next card every 3 seconds
                        setInterval(nextCard, 3000);

                    });

                    
                                                    
                    
                
            </script>
                                  
            <div class="promotion-text">
                Empower Your Workflow – Use the Chatbot for Instant Assistance!
            </div>
                                  
            <div class="card-container">
                <div class="card">Provides real-time error resolutions</div>
                <div class="card">Get Access to necessary files/Manuals</div>
                <div class="card">Answers frequently asked questions</div>
                <div class="card">Connects you with the right support team</div>
            </div>

        </body>
        </html>
    ''')
def extract_urls(text):
    # Simple regex to extract URLs from the text
    url_pattern = r'(https?://[^\s]+)'
    return re.findall(url_pattern, text)

def query_rag(query_text: str):
    # Handle simple greetings or casual conversation
    if query_text.lower() in ['hi', 'hello', 'hey']:
        return "Hello! How can I assist you today?\n I'm AI Assistant tool to answer questions, resolve errors and provide user manuals for SAP"
    elif query_text.lower() in ['how are you?', 'how are u?', 'how are you', 'how are u']:
        return "I'm doing well!, how about you?"
  

    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=2)

    if not results:
        # Return a default response if no relevant results are found
        return "Sorry, I don't understand your question. Please try asking something else."
    
    
  
    

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    # Extract URLs from the context
    urls = extract_urls(context_text)

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    model = Ollama(model="mistral")
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"{response_text}\n\nSources:\n" + "\n".join(f"- {source}" for source in sources)
    # return formatted_response

      # If URLs are found, include them in the response
    if urls:
        formatted_response += "\n\nHere are some relevant links from the documents:\n" + "\n".join(urls)

    return formatted_response


if __name__ == "__main__":
    app.run(debug=True)


