def serialize_project(project):
    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
