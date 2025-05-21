from flask import jsonify
from app.models import User, Task
from app import db
import pandas as pd


def validate_uploaded_file(file):
    FILE_SIZE_LIMIT_IN_MB = 2
    FILE_SIZE_LIMIT_IN_BYTES = FILE_SIZE_LIMIT_IN_MB * 1024 * 1024

    # chcek file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > FILE_SIZE_LIMIT_IN_BYTES:
        return jsonify(
            {"error": f"File size must be less than {FILE_SIZE_LIMIT_IN_MB} MB"}
        )

    # multiple file uploaded - NOT ALLOWED
    if isinstance(file, list) or hasattr(file, "__len__") and len(file) > 1:
        return jsonify({"error": "Only file is allowed"}), 400

    # validate file name and type
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not (file.filename.lower().endswith((".xls", ".xlsx"))):
        return jsonify(
            {"error": "Invalid file type. Only .xls or .xlsx files are allowed"}
        )

    allowed_mimetypes = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]

    if file.mimetype not in allowed_mimetypes:
        return jsonify({"error": "Invalid MIME type for Excel file"}), 400

    return


def process_excel_data(file, project_id):
    try:
        df = pd.read_excel(file)

        # convert column labels to lowercase
        df.columns = df.columns.str.lower()

        # replace NaN to None
        df = df.astype(object).where(pd.notna(df), None)

        # validate rquired columns
        required_columns = {"name", "due_date"}
        if not required_columns.issubset(df.columns):
            return (
                jsonify({"error": f"Missing required columns: {required_columns}"}),
                400,
            )

        # summary
        tasks_summary = {
            "total_tasks": len(df),
            "created_successfully": 0,
            "failed_to_create": 0,
        }

        # inserting into db
        for _, row in df.iterrows():
            try:
                name = row["name"]
                description = row.get("description")
                status = (
                    "_".join(row.get("status").upper().split(" "))
                    if row.get("status")
                    else row.get("status")
                )
                due_date = row["due_date"]
                users = row.get("users")

                task = Task(
                    name=name,
                    description=description,
                    status=status,
                    due_date=due_date,
                    project_id=project_id,
                )
                # TODO
                if users:
                    print(users)
                    users_queryset = User.query.filter(User.name.in_(users)).all()
                    task.users.extend(users_queryset)
                db.session.add(task)
                db.session.commit()
                tasks_summary["created_successfully"] += 1
            except Exception as err:
                tasks_summary["failed_to_create"] += 1
                print(err)

        return tasks_summary

    except Exception as e:
        print(e)
