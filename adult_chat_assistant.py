import streamlit as st
import groq
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Load the new API key from the environment
new_api_key = os.getenv("NEW_API_KEY")

# Function to call Groq API
def call_groq_api(prompt):
    url = "https://api.groq.com/v1/endpoint"  # Replace with the actual endpoint
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {"prompt": prompt}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Parse chat history into structured messages
def parse_chat_history(chat_history):
    messages = []
    lines = chat_history.strip().split("\n")
    i = 0
    while i < len(lines):
        header = lines[i].split(": ", 1)
        if len(header) == 2:
            sender, timestamp = header
            message_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("REPORT"):
                message_lines.append(lines[i].strip())
                i += 1
            message = " ".join(message_lines)
            messages.append({
                "sender": sender.strip(),
                "timestamp": timestamp.strip(),
                "message": message,
            })
        i += 1
    return messages

# Validate responses to ensure compliance with rules
def validate_response(response):
    # Simplify response validation to remove unwanted phrases without disclaimers
    meeting_phrases = [
        "when we meet", "see each other", "meet up someday"
    ]

    for phrase in meeting_phrases:
        if phrase in response:
            response = response.replace(phrase, "")  # Remove the phrase

    boring_phrases = [
        "We can take things one step at a time", 
        "let's cherish the moment",
        "look forward to the possibility of a beautiful connection"
    ]

    for phrase in boring_phrases:
        if phrase in response:
            response = response.replace(phrase, "")  # Remove the phrase

    if "looking forward" in response.lower() or "let's continue chatting" in response.lower():
        response = response.replace("looking forward", "")
        response = response.replace("let's continue chatting", "")

    # Ensure length is within bounds
    if len(response) < 160:
        response += "..."  # Add a placeholder to extend the response naturally

    return response

# Generate responses based on chat history and current message
def generate_responses(chat_history, current_message, tone, temperature):
    try:
        messages = parse_chat_history(chat_history)
        recent_context = ""
        if messages:
            recent_messages = messages[-3:]
            recent_context = "\n".join([f"{m['sender']}: {m['message']}" for m in recent_messages])

        # Define system prompts with core rules
        base_prompt = f"""
You are a flirty and engaging female chat partner named Lynn. Your responses should:
1. Reflect the emotional tone of the chat.
2. Be {tone.lower()} and naturally engaging.
3. Respond specifically to the current message without relying on unrelated history.
4. Maintain a feminine and charming tone.
5. Avoid any language implying future actions or promises unless explicitly requested.
6. Avoid repetitive or boring replies like 'let's continue chatting here for a while'.

Recent Chat History:
{recent_context}

Current Message:
{current_message}

Craft a response that matches the chat's tone and mood without making promises.
        """

        # Select API key based on tone
        if tone in ["Assertive", "Playful"]:
            client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        else:
            client = groq.Groq(api_key=os.getenv("NEW_API_KEY"))

        # Generate response
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": f"His message: {current_message}"},
            ],
            model="mixtral-8x7b-32768",
            temperature=temperature,
            max_tokens=300
        )

        response = completion.choices[0].message.content.strip()
        return validate_response(response)

    except Exception as e:
        return f"Error generating response: {str(e)}"

# Simplified and modern Streamlit UI
def setup_ui():
    st.title("Flirty Chat Assistant")
    st.markdown("Generate engaging responses for your dating site messages.")

    # Input fields
    chat_history = st.text_area("Chat History:", height=300)
    current_message = st.text_area("Current Message:", height=100)

    tone = st.selectbox("Response Tone:", ["Assertive", "Playful", "Charming", "Seductive"])
    temperature = st.slider("Creativity (Temperature):", 0.0, 1.0, 0.7)

    return chat_history, current_message, tone, temperature

# Main UI setup
chat_history, current_message, tone, temperature = setup_ui()

# Generate and display response
if st.button("Generate Response"):
    if not chat_history or not current_message:
        st.error("Please provide both chat history and the current message!")
    else:
        with st.spinner("Crafting the perfect response..."):
            response = generate_responses(chat_history, current_message, tone, temperature)
            st.subheader("Generated Response:")
            st.write(response, unsafe_allow_html=True)
