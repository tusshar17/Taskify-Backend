from flask import jsonify


def get_instance_or_404(model_class, object_id, id_field="id", label=None):
    """
    Generic function to fetch a model instance by its ID with a 404 response.

    :param model_class: SQLAlchemy model class (e.g., User, Project, Task)
    :param object_id: ID value to search by
    :param id_field: Field name to match against (default is "id")
    :param label: Human-readable name for error message (defaults to model name)
    :return: (instance or None, error_response or None, status_code or None)
    """

    model_field = getattr(model_class, id_field)
    instance = model_class.query.filter(model_field == object_id).first()

    if not instance:
        model_name = label or model_class.__name__
        return (
            None,
            jsonify({"error": f"{model_name} not found with {id_field} {object_id}"}),
            404,
        )

    return instance, None, None
