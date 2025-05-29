from flask import Flask, render_template, request, send_file
import google.generativeai as genai
from fpdf import FPDF
import re
import os

# Setup your API key here
genai.configure(api_key="AIzaSyBrBiIp5OcAGSSC1SIaqg0dac-uX5uNqFM")
model = genai.GenerativeModel("models/gemini-1.5-flash")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('form.html')

def parse_section(text, section_name):
    """Extract section text between section headers, or empty string if not found."""
    pattern = rf"{section_name}:\n(.*?)(\n[A-Z][a-zA-Z\s/&]+:|\Z)"
    match = re.search(pattern, text, re.S)
    if match:
        return match.group(1).strip()
    return ""

@app.route('/generate', methods=['POST'])
def generate():
    name = request.form['name']
    email = request.form['email']
    linkedin = request.form['linkedin']
    github = request.form['github']
    leetcode = request.form.get('leetcode', '')
    portfolio = request.form.get('portfolio', '')
    skills = request.form['skills']
    career_goal = request.form.get('goal', '')

    # Education fields
    degrees = request.form.getlist('education_degree[]')
    colleges = request.form.getlist('education_college[]')
    batches = request.form.getlist('education_batch[]')
    cgpas = request.form.getlist('education_cgpa[]')

    education_list = []
    for degree, college, batch, cgpa in zip(degrees, colleges, batches, cgpas):
        if degree.strip() or college.strip():
            edu_line = f"{degree} from {college}, Batch {batch}, CGPA: {cgpa}"
            education_list.append(edu_line)
    education = "\n".join(education_list)

    # Work Experience bullet points (generated separately)
    work_titles = request.form.getlist('work_title[]')
    work_points = []
    for title in work_titles:
        if title.strip():
            prompt = f"Write 3 strong resume bullet points for work experience titled: {title}"
            response = model.generate_content(prompt)
            work_points.append(f"{title}:\n- " + response.text.replace('\n', '\n- '))

    # Projects bullet points
    project_titles = request.form.getlist('project_title[]')
    project_points = []
    for title in project_titles:
        if title.strip():
            prompt = f"Write 3 bullet points for a project titled: {title}"
            response = model.generate_content(prompt)
            project_points.append(f"{title}:\n- " + response.text.replace('\n', '\n- '))

    # Certifications, Achievements, Roles bullet points
    certifications = request.form.getlist('certification_title[]')
    cert_years = request.form.getlist('certification_year[]')
    achievements = request.form.getlist('achievement_title[]')
    achievement_years = request.form.getlist('achievement_year[]')
    roles = request.form.getlist('role_title[]')
    role_years = request.form.getlist('role_year[]')

    cert_output = []
    for title, year in zip(certifications, cert_years):
        if title.strip():
            prompt = f"Write 1 bullet point for certification: {title} ({year})"
            response = model.generate_content(prompt)
            cert_output.append(f"{title} ({year}):\n- {response.text}")

    achievement_output = []
    for title, year in zip(achievements, achievement_years):
        if title.strip():
            prompt = f"Write 1 bullet point for achievement: {title} ({year})"
            response = model.generate_content(prompt)
            achievement_output.append(f"{title} ({year}):\n- {response.text}")

    role_output = []
    for title, year in zip(roles, role_years):
        if title.strip():
            prompt = f"Write 1 bullet point for role or activity: {title} ({year})"
            response = model.generate_content(prompt)
            role_output.append(f"{title} ({year}):\n- {response.text}")

    # Big structured prompt for summary, cover letter, career growth, ideal roles
    big_prompt = f"""
Create a professional resume summary and career advice based on the following info:

Name: {name}
Email: {email}
LinkedIn: {linkedin}
GitHub: {github}
LeetCode: {leetcode}
Portfolio: {portfolio}
Education:
{education}

Skills:
{skills}

Career Goal:
{career_goal}

Please output in EXACT format:
Name: {name}
Email: {email}
inkedIn: {linkedin}
GitHub: {github}
LeetCode: {leetcode}
Portfolio: {portfolio}

Summary:
<One paragraphs summary highlighting skills and background>

Education:
{education}

Work Experince:
{work_points}

Project:
{project_points}

Skills:
{skills}

Certification:
{cert_output}

Role and Activites:
{role_output}

Achivements:
{achievement_output}

Cover Letter:
<One paragraph cover letter tailored to career goal>

Career Growth Suggestion:
<List 2-3 suggestions for career growth in bullet points>

Ideal Career Paths/Job Roles:
<List 3 ideal job roles with a short reason each>

End.
"""

    response = model.generate_content(big_prompt)
    structured_text = response.text.strip()

    # Parse sections
    summary = parse_section(structured_text, "Summary")
    cover_letter = parse_section(structured_text, "Cover Letter")
    growth_suggestions = parse_section(structured_text, "Career Growth Suggestion")
    ideal_roles = parse_section(structured_text, "Ideal Career Paths/Job Roles")

    # ==== BUILDING PDF CONTENT ====
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)

    def write_section(title, content):
        pdf.set_font("DejaVu", 'B', 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("DejaVu", '', 12)
        for line in content.strip().split('\n'):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                pdf.cell(10)
            pdf.multi_cell(0, 8, line)
        pdf.ln(5)

    write_section("Name", name)
    write_section("Personal Platforms", f"Email: {email}\nLinkedIn: {linkedin}\nGitHub: {github}\nLeetCode: {leetcode}\nPortfolio: {portfolio}")

    write_section("Summary", summary)
    write_section("Cover Letter", cover_letter if cover_letter else "No cover letter provided.")

    if education:
        edu_text = '\n'.join([f"- {line}" for line in education_list])
        write_section("Education", edu_text)

    skills_text = '\n'.join([f"- {skill.strip()}" for skill in skills.split(',')])
    write_section("Skills", skills_text)

    write_section("Work Experience", "\n\n".join(work_points) if work_points else "No work experience provided.")
    write_section("Projects", "\n\n".join(project_points) if project_points else "No projects provided.")
    write_section("Certifications", "\n\n".join(cert_output) if cert_output else "No certifications provided.")
    write_section("Achievements", "\n\n".join(achievement_output) if achievement_output else "No achievements provided.")
    write_section("Roles & Activities", "\n\n".join(role_output) if role_output else "No roles or activities provided.")

    write_section("Career Suggestions", growth_suggestions if growth_suggestions else "No suggestions provided.")
    write_section("Career Roadmap", ideal_roles if ideal_roles else "No roadmap provided.")

    pdf.output("resume.pdf")

    return """
    <h2>✅ Resume Generated Successfully!</h2>
    <a href='/download'>📥 Download Resume (PDF)</a>
    """

@app.route('/download')
def download():
    return send_file("resume.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
