import random
import requests
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ==============================
# Facebook Settings
# ==============================
PAGE_TOKEN = "EAAXEooyXjaoBR0DzP4ppJZB877OR3H2bz5QNCJAkB9MIIIIV4jZByXgRXq5s9bGet5KHL580zE2tP6egcrijvxFOeWflBu913x3VZCLjSSkjfuJz1ZBqobyZCsm5Ph39bgNx5giuwCMHfZBZC8ElW2GpxPczZAhI0JIcBCUeiIpjTKjInjseHfripp86YMmjh9H2UUDZB"
PAGE_ID = "1284133118105694"
URL = f"https://graph.facebook.com/v23.0/{PAGE_ID}/feed"

# ==============================
# Subjects
# ==============================

subjects = {
    "Agricultural Sciences": "Agriculture.json",
    "Business Studies": "Business.json",
    "Economics": "Economics.json",
    "Geography": "Geography.json",
    "History": "History.json",
    "Life Sciences": "LifeSciences.json",
    "Mathematics": "Maths.json",
    "Mathematical Literacy": "ML.json",
    "Physical Sciences": "Physics.json",
    "My Children!, My Africa!": "MCMA.json"
}

# ==============================
# Find subjects that still have questions
# ==============================

available_subjects = []

for subject, filename in subjects.items():

    if not os.path.exists(filename):
        continue

    with open(filename, "r", encoding="utf-8") as file:
        questions = json.load(file)

    if len(questions) > 0:
        available_subjects.append(subject)

# ==============================
# Stop if everything has been posted
# ==============================

if len(available_subjects) == 0:

    print("All questions have been posted!")
    quit()

# ==============================
# Choose random subject
# ==============================

subject = random.choice(available_subjects)
filename = subjects[subject]

# Load questions

with open(filename, "r", encoding="utf-8") as file:
    questions = json.load(file)

# Choose random question

randomQuestion = random.choice(questions)

print(f"Subject: {subject}")
print(f"Question: {randomQuestion['id']}")

# ==============================
# Facebook Post
# ==============================

payload = {
    "message": f"📚 {subject}\n\n{randomQuestion['question']}",
    "access_token": PAGE_TOKEN
}

response = requests.post(URL, data=payload)

print(response.status_code)
print(response.text)

# ==============================
# Delete question only if post succeeded
# ==============================

if response.status_code == 200:

    questions.remove(randomQuestion)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            questions,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f" Posted and removed {randomQuestion['id']}")

else:

    print("Facebook rejected the post.")
    print("Question was NOT removed.")