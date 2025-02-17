import streamlit as st
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key securely
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API Key not found! Please set it in the .env file.")
    st.stop()

# Configure Gemini AI
genai.configure(api_key=api_key)

# Initialize session state variables
if "questions" not in st.session_state:
    st.session_state.questions = []
if "selected_options" not in st.session_state:
    st.session_state.selected_options = []
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_level" not in st.session_state:
    st.session_state.quiz_level = None
if "text_content" not in st.session_state:
    st.session_state.text_content = ""

@st.cache_data
def fetch_questions(text_content, quiz_level):
    RESPONSE_JSON = {
        "mcqs": [
            {
                "mcq": "Sample multiple choice question1",
                "options": {
                    "a": "Choice 1",
                    "b": "Choice 2",
                    "c": "Choice 3",
                    "d": "Choice 4",
                },
                "correct": "a",
            }
        ]
    }

    PROMPT_TEMPLATE = f"""
    Text: {text_content}
    You are an expert in generating MCQ quizzes based on the provided content.
    Given the above text, create a quiz of at least 10 multiple choice questions with a difficulty level of {quiz_level}.
    Make sure the questions are unique, non-repetitive, and relevant.

    Format the response strictly as JSON in this structure:
    {json.dumps(RESPONSE_JSON, indent=2)}
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(PROMPT_TEMPLATE)

        # Ensure response is in JSON format
        extracted_response = response.text.strip()
        extracted_response = extracted_response.replace("```json", "").replace("```", "").strip()

        return json.loads(extracted_response).get("mcqs", [])

    except json.JSONDecodeError:
        st.error("Error: Gemini API response is not valid JSON. Try again.")
        return []
    except Exception as e:
        st.error(f"Error fetching quiz: {e}")
        return []

def main():
    st.title("Quiz Generator App")

    if not st.session_state.quiz_started:
        # Get user input
        st.session_state.text_content = st.text_area("Paste the text content here:", value=st.session_state.text_content)
        st.session_state.quiz_level = st.selectbox("Select quiz level:", ["Easy", "Medium", "Hard"], index=0)

        if st.button("Generate Quiz"):
            st.session_state.questions = fetch_questions(st.session_state.text_content, st.session_state.quiz_level.lower())
            st.session_state.selected_options = [None] * len(st.session_state.questions)
            st.session_state.quiz_started = True
            st.rerun()

    else:
        # Display quiz questions
        st.subheader("Quiz Questions")
        for i, question in enumerate(st.session_state.questions):
            options = list(question["options"].values())
            st.session_state.selected_options[i] = st.radio(
                question["mcq"], options, index=None, key=f"q{i}"
            )

        # Submit button
        if st.button("Submit"):
            marks = 0
            st.header("Quiz Result:")
            for i, question in enumerate(st.session_state.questions):
                st.subheader(question["mcq"])
                st.write(f"You selected: {st.session_state.selected_options[i]}")
                correct_answer = question["options"][question["correct"]]
                st.write(f"Correct answer: {correct_answer}")

                if st.session_state.selected_options[i] == correct_answer:
                    marks += 1

            st.subheader(f"You scored {marks} out of {len(st.session_state.questions)}")

            # Reset quiz state after showing results
            if st.button("Restart Quiz"):
                st.session_state.quiz_started = False
                st.session_state.questions = []
                st.session_state.selected_options = []
                st.session_state.text_content = ""
                st.rerun()

if __name__ == "__main__":
    main()
