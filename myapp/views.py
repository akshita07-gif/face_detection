from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, date, time
from werkzeug.security import check_password_hash
import cv2
import face_recognition
import numpy as np
import os

from .db import admins_col, students_col, attendances_col


# ================= LOGIN =================
def login_view(request):

   

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        admin = admins_col.find_one({"username": username})

        if admin and check_password_hash(admin["password"], password):

            request.session["admin"] = username
            return redirect("home")

        else:
            messages.error(request, "Invalid Username or Password")

    return render(request, "login.html")


# ================= LOGOUT =================
def logout_view(request):

    request.session.flush()
    return redirect("login")


# ================= HOME =================
def home(request):

    if "admin" not in request.session:
        return redirect("login")

    return render(request, "index.html")


# ================= DASHBOARD =================
def dashboard(request):

    total_students = students_col.count_documents({})

    today = str(date.today())
    today_attendance = attendances_col.count_documents({"date": today})

    total_records = attendances_col.count_documents({})

    context = {
        "total_students": total_students,
        "today_attendance": today_attendance,
        "total_records": total_records
    }

    return render(request,"dashboard.html",context)


# ================= REGISTER STUDENT =================
def register_student(request):

    if "admin" not in request.session:
        return redirect("login")

    if request.method == "POST":

        name = request.POST.get("name")
        roll = request.POST.get("roll")
        file = request.FILES.get("image")

        if file:

            path = os.path.join("media", file.name)

            with open(path, "wb+") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            students_col.insert_one({
                "name": name,
                "roll": roll,
                "image": path
            })

            messages.success(request, "Student Registered Successfully")

    return render(request, "register.html")

# ================= FACE ATTENDANCE =================

def mark_attendance(request):

    if "admin" not in request.session:
        return redirect("login")

    students = list(students_col.find())

    known_faces = []
    known_rolls = []

    print("Loading student images...")

    # Load student images and create encodings
    for student in students:
        try:
            img = face_recognition.load_image_file(student["image"])
            encode = face_recognition.face_encodings(img)

            if len(encode) > 0:
                known_faces.append(encode[0])
                known_rolls.append(student["roll"])
                print("Encoding loaded for:", student["roll"])
            else:
                print("No face found in:", student["image"])

        except Exception as e:
            print("Error:", e)

    if len(known_faces) == 0:
        messages.error(request, "No student faces found")
        return redirect("dashboard")

    cam = cv2.VideoCapture(0)

    today = str(date.today())

    while True:

        ret, frame = cam.read()

        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = face_recognition.face_locations(rgb)
        encodes = face_recognition.face_encodings(rgb, faces)

        for encodeFace, faceLoc in zip(encodes, faces):

            matches = face_recognition.compare_faces(known_faces, encodeFace, tolerance=0.55)
            faceDis = face_recognition.face_distance(known_faces, encodeFace)

            if len(faceDis) == 0:
                continue

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:

                roll = known_rolls[matchIndex]

                print("Face matched:", roll)

                already = attendances_col.find_one({
                    "roll": roll,
                    "date": today
                })

                if not already:

                    attendances_col.insert_one({
                        "roll": roll,
                        "date": today,
                        "status": "Present",
                        "time": datetime.now().strftime("%H:%M:%S")
                    })

                    print("Attendance saved for:", roll)

                top, right, bottom, left = faceLoc

                cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                cv2.putText(frame, roll, (left, top-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        cv2.imshow("Face Attendance Camera", frame)

        if cv2.waitKey(1) == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    messages.success(request, "Attendance Completed")

    return redirect("dashboard")
# ================= AUTO ABSENT AFTER 5PM =================
def auto_mark_absent():

    today = str(date.today())

    now = datetime.now().time()

    if now >= time(17,0):

        students = list(students_col.find())

        for student in students:

            already = attendances_col.find_one({
                "roll": student["roll"],
                "date": today
            })

            if not already:

                attendances_col.insert_one({
                    
                    "roll": student["roll"],
                    "date": today,
                    "status": "Absent",
                    "time": "17:00"
                })


# ================= REPORTS =================
def reports(request):

    data = list(attendances_col.find().sort("date",-1))

    return render(request,"reports.html",{"data":data})
