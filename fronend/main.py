from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import docx
import glob
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow requests from any origin

# Direct API key configuration - no .env file needed
# IMPORTANT: Replace this with your actual Groq API key
GROQ_API_KEY = "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"  # Replace with your actual key

# Load company data from multiple Word documents
def load_company_info_from_dir(docs_dir="doc"):
    all_docs_content = []
    
    # Find all .docx files in the specified directory
    doc_files = glob.glob(f"{docs_dir}/*.docx")
    
    for doc_file in doc_files:
        try:
            doc = docx.Document(doc_file)
            
            # Extract text from paragraphs, filtering out empty ones
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            
            # NEW: Remove repetitive content by deduplicating similar sentences
            cleaned_paragraphs = []
            seen_phrases = set()
            
            for para in paragraphs:
                # Skip paragraphs that are very similar to ones we've seen
                is_duplicate = False
                for seen in seen_phrases:
                    if para in seen or seen in para or similarity_check(para, seen):
                        is_duplicate = True
                        break
                
                if not is_duplicate and not is_repetitive(para):
                    cleaned_paragraphs.append(para)
                    seen_phrases.add(para)
            
            # Join the cleaned paragraphs
            content = "\n".join(cleaned_paragraphs)
            
            # Add document name as header for better context
            filename = os.path.basename(doc_file)
            all_docs_content.append(f"--- {filename} ---\n{content}")
        except Exception as e:
            print(f"Error loading {doc_file}: {e}")
    
    # Combine all documents into a single string
    return "\n\n".join(all_docs_content)

# Helper function to detect repetitive content
def is_repetitive(text):
    # Detect sentences or phrases that repeat within the same paragraph
    words = text.split()
    if len(words) < 10:  # Skip very short texts
        return False
        
    # Check for repeating patterns within the text
    segments = []
    for i in range(len(words) - 3):
        segments.append(" ".join(words[i:i+3]))
    
    # Count occurrences of each 3-word segment
    counts = {}
    for segment in segments:
        counts[segment] = counts.get(segment, 0) + 1
    
    # If any 3-word segment occurs more than twice, consider it repetitive
    for segment, count in counts.items():
        if count > 2 and len(segment) > 10:  # Avoid counting common short phrases
            return True
    
    return False

# Helper function to check if two strings are very similar
def similarity_check(str1, str2):
    # Simple similarity check - if the strings share a lot of content
    if len(str1) < 20 or len(str2) < 20:  # Skip very short strings
        return False
        
    # Check if they share significant content
    common_words = set(str1.lower().split()) & set(str2.lower().split())
    total_words = set(str1.lower().split()) | set(str2.lower().split())
    
    # If they share more than 70% of their words, consider them similar
    similarity = len(common_words) / len(total_words) if total_words else 0
    return similarity > 0.7

# Load all documents during startup
company_info = load_company_info_from_dir()
print(f"Loaded {len(glob.glob('doc/*.docx'))} documents")

# Setup LangChain + Groq
llm = ChatGroq(
    model="gemma2-9b-it",  # or "mixtral-8x7b", etc.
    api_key=GROQ_API_KEY,
    temperature=0.3,  # Lower temperature for more focused responses
    max_tokens=800    # Limit response length to avoid rambling
)

# IMPROVED: Better prompt template with clear instructions and examples
prompt_template = """
You are a helpful customer service assistant for Digitizers Academy. Your task is to provide clear, accurate responses based on the company information below.

COMPANY INFORMATION:
{company_info}

IMPORTANT INSTRUCTIONS:
1. Answer ONLY based on the company information provided above.
2. If the answer isn't in the company information, say: "I don't have that information available."
3. Keep responses concise and to the point - no more than 2-3 paragraphs.
4. Do NOT repeat phrases like "Let me know if you have any other questions" multiple times.
5. Be conversational but professional.
6. Focus on giving direct answers to questions without unnecessary text.

USER QUESTION: {question}

YOUR RESPONSE:
"""

prompt = PromptTemplate(
    input_variables=["company_info", "question"],
    template=prompt_template
)

# Use the modern approach with runnables
def format_prompt(inputs):
    return prompt.format(company_info=inputs["company_info"], question=inputs["question"])

qa_chain = (
    RunnablePassthrough() 
    | format_prompt 
    | llm
)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')  # '.' means current directory

@app.route('/docs_info', methods=['GET'])
def docs_info():
    """Endpoint to get information about loaded documents"""
    doc_files = glob.glob("doc/*.docx")
    return jsonify({
        "loaded_docs": [os.path.basename(f) for f in doc_files],
        "doc_count": len(doc_files)
    })

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    
    # Input validation
    if not user_input or not user_input.strip():
        return jsonify({"reply": "Please enter a question."})
    
    try:
        # Use invoke method instead of run
        response = qa_chain.invoke({
            "company_info": company_info, 
            "question": user_input
        })
        
        # Extract just the content from the response
        reply = response.content if hasattr(response, 'content') else str(response)
        
        # IMPROVED: Enhanced response cleaning to prevent repetitive phrases
        cleaned_reply = clean_response(reply)
        
        return jsonify({"reply": cleaned_reply})
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"reply": "I'm sorry, I encountered an error processing your request. Please try again."})

# Helper function to clean repetitive content from responses
def clean_response(text):
    # 1. Remove duplicate sentences
    sentences = text.split('. ')
    unique_sentences = []
    seen = set()
    
    for sentence in sentences:
        clean_sent = sentence.strip().lower()
        if clean_sent not in seen and not any(similarity_check(clean_sent, s) for s in seen):
            seen.add(clean_sent)
            unique_sentences.append(sentence)
    
    # 2. Handle common repetitive phrases
    repetitive_patterns = [
        "Let me know what you're interested in",
        "Let me know if you have any other questions",
        "What are you looking to learn",
        "I'll help you find the perfect program for you",
        "Let me know what you'd like to"
    ]
    
    text = '. '.join(unique_sentences)
    
    # Count occurrences of repetitive patterns
    for pattern in repetitive_patterns:
        if text.lower().count(pattern.lower()) > 1:
            # Find first occurrence (case-insensitive)
            i = text.lower().find(pattern.lower())
            if i >= 0:
                # Keep only the first occurrence with proper case
                actual_case = text[i:i+len(pattern)]
                text = text.replace(pattern, "").replace(actual_case, pattern)
                text = text.replace("  ", " ").replace(" .", ".").replace("..", ".")
    
    # 3. Final cleanup of any awkward punctuation from our processing
    text = text.replace(" .", ".").replace("..", ".").replace(". .", ".")
    
    return text
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)