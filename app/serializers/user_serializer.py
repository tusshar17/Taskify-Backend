def serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }
