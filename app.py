from flask import Flask, render_template, request
import pymupdf
import re

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

SKILLS = [
    "python", "java", "c++", "javascript", "html", "css",
    "flask", "django", "sql", "mysql", "mongodb",
    "machine learning", "data analysis", "pandas", "numpy",
    "git", "github", "rest api", "aws", "docker",
    "communication", "problem solving", "linux", "react",
    "node.js", "excel", "power bi", "tableau", "c"
]

def extract_text(file):
    content = file.read()
    with pymupdf.open(stream=content, filetype="pdf") as pdf:
        return "\n".join(page.get_text() for page in pdf)

def find_skills(text):
    text = text.lower()
    found = []
    for skill in SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            found.append(skill)
    return found

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        resume = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not resume or not resume.filename:
            error = "Please upload your PDF resume."
        elif not resume.filename.lower().endswith(".pdf"):
            error = "Please upload a PDF resume only."
        elif not job_description:
            error = "Please enter the job description."
        else:
            try:
                resume_text = extract_text(resume)
                if not resume_text.strip():
                    error = "No readable text found. Try a text-based PDF."
                else:
                    resume_skills = find_skills(resume_text)
                    required_skills = find_skills(job_description)
                    matched = [s for s in required_skills if s in resume_skills]
                    missing = [s for s in required_skills if s not in resume_skills]
                    score = round(len(matched) / len(required_skills) * 100) if required_skills else 0

                    suggestions = []
                    if not required_skills:
                        suggestions.append("The job description contains no recognized skills. Add specific technical or professional requirements.")
                    if missing:
                        suggestions.append("Review these skills and add them only if you genuinely have them: " + ", ".join(missing))
                    if len(resume_text.split()) < 150:
                        suggestions.append("Your resume appears short. Consider adding relevant projects, education, and experience.")
                    if not suggestions:
                        suggestions.append("Good keyword coverage. Tailor your experience and achievements to the role.")

                    result = {
                        "score": score,
                        "matched": matched,
                        "missing": missing,
                        "resume_skills": resume_skills,
                        "suggestions": suggestions,
                        "word_count": len(resume_text.split()),
                        "required_count": len(required_skills)
                    }
            except Exception:
                error = "Could not read this PDF. Please try another text-based PDF."

    return render_template("index.html", result=result, error=error)

@app.errorhandler(413)
def too_large(error):
    return "PDF too large. Please upload a file smaller than 10 MB.", 413

if __name__ == "__main__":
    app.run(debug=True)
