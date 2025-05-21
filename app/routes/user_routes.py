from flask import Blueprint, request, jsonify
from app.models import User
from app.utils.db_helpers import get_instance_or_404
from app.serializers import serialize_user
from app import db

user_bp = Blueprint("user_bp", __name__)


# get all users - paginated and sorted
@user_bp.route("/", methods=["GET"])
def get_users():
    # query params for pagination and sorting
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    sort_by = request.args.get("sort_by", "updated_at")
    order = request.args.get("order", "desc")

    # validate sort_by argument value
    if sort_by not in ["name", "created_at", "updated_at"]:
        return jsonify({"error": "Invalid sort_by field"}), 400
    sort_column = getattr(User, sort_by)
    # sorting order - descending or ascending
    if order == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    user_paginated = User.query.order_by(sort_column).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "total": user_paginated.total,
                "pages": user_paginated.pages,
                "current_page": user_paginated.page,
                "users": [serialize_user(user) for user in user_paginated.items],
            }
        ),
        200,
    )


# get a user by id
@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    user, error_response, status_code = get_instance_or_404(
        User, user_id, "id", label="User"
    )
    if error_response:
        return error_response, status_code
    return (
        jsonify(serialize_user(user)),
        200,
    )


# create a user
@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    name = data.get("name")

    # required fields validation
    if not name:
        return jsonify({"error": "User Name is required"}), 400

    user = User(name=name)

    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)

    return (
        jsonify(
            {
                "message": "User created successfully",
                "user": serialize_user(user),
            }
        ),
        201,
    )


# update a user by id
@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user, error_response, status_code = get_instance_or_404(
        User, user_id, "id", label="User"
    )
    if error_response:
        return error_response, status_code

    data = request.get_json()
    user.name = data.get("name", user.name)

    db.session.commit()
    db.session.refresh(user)

    return (
        jsonify(
            {
                "message": "User updated successfully",
                "user": serialize_user(user),
            }
        ),
        200,
    )


# delete a user by id
@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user, error_response, status_code = get_instance_or_404(
        User, user_id, "id", label="User"
    )
    if error_response:
        return error_response, status_code

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"})
