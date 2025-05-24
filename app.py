from flask import Flask, render_template, request, send_file
import google.generativeai as genai
import os
from dotenv import load_dotenv
from fpdf import FPDF

genai.configure(api_key="AIzaSyBrBiIp5OcAGSSC1SIaqg0dac-uX5uNqFM")
model = genai.GenerativeModel("models/gemini-1.5-flash")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('form.html')



import unicodedata

def clean_text(text):
    # Normalize text to remove fancy characters
    text = unicodedata.normalize("NFKD", text)
    # Remove characters that can't be encoded in latin-1
    return text.encode('latin-1', 'ignore').decode('latin-1')

@app.route('/generate', methods=['POST'])
def generate():
    name = request.form['name']
    education = request.form['education']
    skills = request.form['skills']
    experience = request.form['experience']
    career_goal = request.form['goal']

    prompt = f"""
    Create a professional resume for:
    Name: {name}
    Education: {education}
    Skills: {skills}
    Experience: {experience}
    Career Goal: {career_goal}

    Format it well. Provide a 1-paragraph cover letter and a career growth suggestion.
    Also suggest 3 ideal career paths or job roles that match this candidate’s profile, with one-sentence reasons.
    """

    response = model.generate_content(prompt)
    output = clean_text(response.text)

    # Extract Career Growth Suggestion and Career Paths
    career_suggestion = ""
    career_paths = ""

    if "**Career Growth Suggestion:**" in output:
        parts = output.split("**Career Growth Suggestion:**", 1)
        # parts[1] contains everything after the suggestion header

        # Now split at Ideal Career Paths header if present
        if "**Ideal Career Paths/Job Roles:**" in parts[1]:
            suggestion_part, paths_part = parts[1].split("**Ideal Career Paths/Job Roles:**", 1)
            career_suggestion = suggestion_part.strip().replace('---','').strip()
            career_paths = paths_part.strip()
        else:
            career_suggestion = parts[1].strip()

    else:
        career_suggestion = "No career growth suggestion found."
        career_paths = "No career paths found."

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add main content (resume & cover letter)
    main_content = output.split("**Career Growth Suggestion:**")[0]
    for line in main_content.split('\n'):
        pdf.multi_cell(0, 10, line)

    # Add Career Growth Suggestion section heading
    pdf.ln(10)  # add some vertical space
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Career Growth Suggestion:", ln=True)
    pdf.set_font("Arial", size=12)
    for line in career_suggestion.split('\n'):
        pdf.multi_cell(0, 10, line)

    # Add Ideal Career Paths section heading
    pdf.ln(10)  # vertical space
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Ideal Career Paths / Job Roles:", ln=True)
    pdf.set_font("Arial", size=12)
    for line in career_paths.split('\n'):
        pdf.multi_cell(0, 10, line)

    pdf_file = "resume.pdf"
    pdf.output(pdf_file)

    # Return nicely formatted output with suggestions separately shown
    return f"""
    <h2>Resume & Cover Letter</h2>
    <pre>{main_content}</pre>
    <hr>
    <h2>🚀 Career Growth Suggestion</h2>
    <pre>{career_suggestion}</pre>
    <hr>
    <h2>🚀 Ideal Career Paths / Job Roles</h2>
    <pre>{career_paths}</pre>
    <br><a href='/download'>Download Resume (PDF)</a>
    """





@app.route('/download')
def download():
    return send_file("resume.pdf", as_attachment=True)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

