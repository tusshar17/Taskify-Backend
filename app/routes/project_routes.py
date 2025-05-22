from flask import Blueprint, request, jsonify
from app.models import Project
from app import db
from app.utils.db_helpers import get_instance_or_404
from app.serializers import serialize_project

project_bp = Blueprint("project_bp", __name__)


# get multiple projects - paginated and sorted
@project_bp.route("/", methods=["GET"])
def get_projects():
    # query params for pagination and sorting
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    sort_by = request.args.get("sort_by", "updated_at")
    order = request.args.get("order", "desc")

    # validate sort_by argument value
    if sort_by not in ["name", "created_at", "updated_at"]:
        return jsonify({"error": "Invalid sort_by field"}), 400
    sort_column = getattr(Project, sort_by)
    # sorting order - descending or ascending
    if order == "asc":
        sort_column = sort_column.asc()
    else:
        sort_column = sort_column.desc()

    projects_paginated = Project.query.order_by(sort_column).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "total": projects_paginated.total,
                "pages": projects_paginated.pages,
                "current_page": projects_paginated.page,
                "projects": [
                    serialize_project(project) for project in projects_paginated.items
                ],
            }
        ),
        200,
    )


# get a project by id
@project_bp.route("/<int:project_id>", methods=["GET"])
def get_project_by_id(project_id):
    project, error_response, status_code = get_instance_or_404(
        Project, project_id, "id", label="project"
    )
    if error_response:
        return error_response, status_code

    return (
        jsonify(serialize_project(project)),
        200,
    )


# create a project
@project_bp.route("/", methods=["POST"])
def create_project():
    data = request.get_json()
    name = data.get("name")

    # required fields validation
    if not name:
        return jsonify({"error": "Project Name is required"}), 400

    project = Project(name=name)

    db.session.add(project)
    db.session.commit()
    db.session.refresh(project)

    return (
        jsonify(
            {
                "message": "Project created successfully",
                "project": serialize_project(project),
            }
        ),
        201,
    )


# update a project by id
@project_bp.route("/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    project, error_response, status_code = get_instance_or_404(
        Project, project_id, "id", label="Project"
    )
    if error_response:
        return error_response, status_code

    data = request.get_json()
    project.name = data.get("name", project.name)

    db.session.commit()
    db.session.refresh(project)

    return (
        jsonify(
            {
                "message": "Project updated successfully",
                "project": serialize_project(project),
            }
        ),
        200,
    )


# delete a project by id
@project_bp.route("/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    project, error_response, status_code = get_instance_or_404(
        Project, project_id, "id", label="Project"
    )
    if error_response:
        return error_response, status_code

    db.session.delete(project)
    db.session.commit()

    return jsonify({"message": "Project deleted successfully"})
