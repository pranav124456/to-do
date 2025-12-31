def user_helper(user):
    return {
        "email": user["email"]
    }

def task_helper(task):
    return {
        "id": str(task["_id"]),
        "title": task["title"],
        "completed": task["completed"]
    }
