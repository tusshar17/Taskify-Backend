from flask import Blueprint, request, jsonify, send_file
from app.models import Task, Project, User
from app.models.task import StatusEnum
from app import db
from app.serializers import serialize_task, serialize_task_for_export
from app.utils.db_helpers import get_instance_or_404
from app.utils.export_tasks import export_tasks
from app.utils.import_tasks import validate_uploaded_file, process_excel_data
from datetime import datetime
import pandas as pd

task_bp = Blueprint("task_bp", __name__)


# get all tasks by project id - paginated and sorted
@task_bp.route("/", methods=["GET"])
def get_tasks(project_id):
    # query params for pagination and sorting
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    sort_by = request.args.get("sort_by", "updated_at")
    order = request.args.get("order", "desc")

    # validate sort_by argument value
    if sort_by not in ["name", "created_at", "updated_at", "due_date"]:
        return jsonify({"error": "Invalid sort_by field"}), 400
    sort_column = getattr(Task, sort_by)
    # sorting order - descending or ascending
    if order == "asc":
        sort_column = sort_column.asc()
    else:
        sort_column = sort_column.desc()

    tasks_paginated = (
        Task.query.filter_by(project_id=project_id)
        .order_by(sort_column)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return (
        jsonify(
            {
                "total": tasks_paginated.total,
                "pages": tasks_paginated.pages,
                "current_page": tasks_paginated.page,
                "tasks": [serialize_task(task) for task in tasks_paginated.items],
            }
        ),
        200,
    )


# get a task by id
@task_bp.route("/<int:task_id>", methods=["GET"])
def get_task_by_id(project_id, task_id):
    task, error_response, status_code = get_instance_or_404(
        Task, task_id, "id", label="Task"
    )
    if error_response:
        return error_response, status_code

    return (
        jsonify(serialize_task(task)),
        200,
    )


# Create a task
@task_bp.route("/", methods=["POST"])
def create_task(project_id):
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    status = data.get("status", StatusEnum.NOT_STARTED)
    due_date_str = data.get("due_date")
    user_ids = data.get("user_ids", [])

    try:
        due_date = datetime.strptime(due_date_str, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        due_date = datetime.fromisoformat(due_date_str)

    # required fields validation
    if not name or not due_date:
        return (
            jsonify({"error": "name and due_date are mandatory fields"}),
            400,
        )

    # check if project exist
    project, error_response, status_code = get_instance_or_404(
        Project, project_id, "id", label="project"
    )
    if error_response:
        return error_response, status_code

    # create the task
    task = Task(
        name=name,
        description=description,
        status=status,
        due_date=due_date,
        project=project,
    )

    if user_ids:
        users = User.query.filter(User.id.in_(user_ids)).all()
        task.users.extend(users)

    db.session.add(task)
    db.session.commit()
    db.session.refresh(task)

    return (
        jsonify(
            {
                "message": "Task created successfully",
                "task": serialize_task(task),
            }
        ),
        200,
    )


# update a task by id
@task_bp.route("/<int:task_id>", methods=["PUT"])
def update_task(project_id, task_id):
    task, error_response, status_code = get_instance_or_404(
        Task, task_id, "id", label="Task"
    )
    if error_response:
        return error_response, status_code

    data = request.get_json()
    task.name = data.get("name", task.name)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)
    task.project_id = data.get("project_id", task.project_id)

    if data.get("due_date"):
        try:
            task.due_date = datetime.strptime(
                data.get("due_date"), "%a, %d %b %Y %H:%M:%S %Z"
            )
        except ValueError:
            due_date = datetime.fromisoformat(data.get("due_date"))

    if data.get("user_ids"):
        new_users = User.query.filter(User.id.in_(data.get("user_ids"))).all()
        new_user_ids = {user.id for user in new_users}
        existing_user_ids = {user.id for user in task.users}

        # Remove users no longer in new_user_ids
        task.users = [user for user in task.users if user.id in new_user_ids]

        # Add users that are new
        users_to_add = [user for user in new_users if user.id not in existing_user_ids]
        task.users.extend(users_to_add)

    db.session.commit()
    db.session.refresh(task)

    return (
        jsonify(
            {
                "message": "Task updated successfully",
                "task": serialize_task(task),
            }
        ),
        200,
    )


# delete a task by id
@task_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_task(project_id, task_id):
    task, error_response, status_code = get_instance_or_404(
        Task, task_id, "id", label="Task"
    )
    if error_response:
        return error_response, status_code

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted successfully"})


# download all tasks by project id
@task_bp.route("/download", methods=["GET"])
def download_file(project_id):
    # check if project exists
    project, error_response, status_code = get_instance_or_404(
        Project, project_id, "id", "Project"
    )
    if error_response:
        return error_response, status_code

    tasks = Task.query.filter_by(project_id=project_id)
    serialized_tasks = [serialize_task_for_export(task) for task in tasks]

    if len(serialized_tasks) < 1:
        return jsonify({"message": "No tasks to download/export"})

    output = export_tasks(serialized_tasks)

    project_name = "-".join(Project.query.get(project_id).name.lower().split(" "))

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{project_name}-tasks.xlsx",
    )


# import tasks from excel file
@task_bp.route("/upload", methods=["POST"])
def import_task_from_excel(project_id):
    # check if project exists
    project, error_response, status_code = get_instance_or_404(
        Project, project_id, "id", "Project"
    )
    if error_response:
        return error_response, status_code

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    validate_uploaded_file(file)

    # process excel file
    task_upload_summary = process_excel_data(file, project_id)

    return jsonify({"task_upload_summary": task_upload_summary}), 200
