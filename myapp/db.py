from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["face_attendances"]

admins_col = db["admins"]
students_col = db["students"]
attendances_col = db["attendances"]
