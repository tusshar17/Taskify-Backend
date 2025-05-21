from app.models import User, Project


def serialize_task(task):
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "status": task.status.value,
        "due_date": task.due_date,
        "project": {"id": task.project_id, "name": task.project.name},
        "user_ids": [user.id for user in task.users],
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def serialize_task_for_export(task):
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "status": task.status.value,
        "due_date": task.due_date.strftime("%Y-%m-%d %H:%M:%S"),
        "project": Project.query.get(task.project_id).name,
        "users": [User.query.get(user.id).name for user in task.users],
        "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": task.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
