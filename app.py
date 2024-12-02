from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
import google.generativeai as genai
import os
import json

# Set your API key securely via environment variables (you can also use dotenv to load them from a .env file)
os.environ["GOOGLE_API_KEY"] = "AIzaSyB_4wPmxxoU-RC7VDe8skmkjqrioEtYhXM"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# app creation
app = Flask(__name__)

# load model
model = genai.GenerativeModel("models/gemini-1.5-pro")


import json

import json

def resumes_details(resume):
    prompt = f"""
    You are a resume parsing assistant. Given the following resume text, extract all the important details and return them in a well-structured JSON format.

    The resume text:
    {resume}

    Extract and include the following:
    - Full Name
    - Contact Number
    - Email Address
    - Location
    - Skills (Technical and Non-Technical, separately if possible)
    - Education
    - Work Experience (including company name, role, and responsibilities)
    - Certifications
    - Languages spoken
    - Suggested Resume Category (based on the skills and experience)
    - Recommended Job Roles (based on the candidate's skills and experience)

    Return the response in JSON format.
    """
    response = model.generate_content(prompt).text
    print("Generated Content:", response)  # Print the raw model response

    # Check if the response is empty or invalid
    if not response:
        print("Empty response received.")
        return None

    # Clean the response (remove the code block markers like '```json')
    response_clean = response.strip()

    # Remove the '```json' and any trailing backticks if they exist
    response_clean = response_clean.replace("```json", "").replace("```", "")

    print("Cleaned Response:", repr(response_clean))

    # Try parsing the response as JSON
    try:
        parsed_data = json.loads(response_clean)  # Attempt to parse as JSON
        print("Parsed JSON:", parsed_data)
        return parsed_data
    except json.JSONDecodeError as e:
        # Print more details to understand what went wrong
        print(f"JSON Decode Error: {e}")
        print("The response is not valid JSON. Here's the response that caused the error:")
        print(repr(response_clean))  # Print the problematic response
        return None

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        # Extract text from the PDF
        text = ""
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()

        # Get resume details from the model
        response = resumes_details(text)
        print("Parsed Response:", response)

        if not response:
            return jsonify({"error": "Failed to process the resume."}), 500

        # Extract details from response
        full_name = response.get("full_name", "N/A")
        contact_number = response.get("contact_number", "N/A")
        email_address = response.get("email_address", "N/A")
        location = response.get("location", "N/A")

        # Extract skills
        skills = response.get("skills", {})
        technical_skills = skills.get("programming", []) + skills.get("web_development", []) + skills.get("technology", [])
        non_technical_skills = []  # Assuming 'non_technical_skills' isn't directly provided in the JSON

        # Convert skills list to string
        technical_skills_str = ", ".join(technical_skills)
        non_technical_skills_str = ", ".join(non_technical_skills)

        # Handle Education
        education = response.get("education", [])
        education_str = "\n".join([
            f"{edu.get('degree', 'N/A')} at {edu.get('institution', 'N/A')} ({edu.get('dates', 'N/A')}, GPA: {edu.get('gpa', 'N/A')})"
            for edu in education
        ])

        # Handle Work Experience
        work_experience = response.get("work_experience", [])
        work_experience_str = "\n".join([
            f"{exp.get('role', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('dates', 'N/A')})\n"
            + "\n".join([f"- {resp}" for resp in exp.get("responsibilities", [])])
            for exp in work_experience
        ])

        # Handle Certifications
        certifications = response.get("certifications", [])
        certifications_str = ", ".join(certifications) if certifications else "N/A"

        # Handle Languages
        languages = response.get("languages", [])
        languages_str = ", ".join(languages) if languages else "N/A"

        # Suggested categories and job roles (if available)
        suggested_resume_category = response.get("suggested_resume_category", "N/A")
        recommended_job_roles = response.get("recommended_job_roles", [])
        recommended_job_roles_str = ", ".join(recommended_job_roles)

        # Render the response to the template
        return render_template(
            'index.html',
            full_name=full_name,
            contact_number=contact_number,
            email_address=email_address,
            location=location,
            technical_skills=technical_skills_str,
            non_technical_skills=non_technical_skills_str,
            education=education_str,
            work_experience=work_experience_str,
            certifications=certifications_str,
            languages=languages_str,
            suggested_resume_category=suggested_resume_category,
            recommended_job_roles=recommended_job_roles_str
        )
    else:
        return jsonify({"error": "Unsupported file format. Please upload a PDF."}), 400

# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)
