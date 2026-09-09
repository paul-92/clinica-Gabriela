import os


def get_initial_admin_config():
    username = os.getenv("INITIAL_ADMIN_USERNAME", "").strip()
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    if bool(username) != bool(password):
        raise RuntimeError("INITIAL_ADMIN_USERNAME e INITIAL_ADMIN_PASSWORD devem ser definidos juntos.")
    if password and len(password) < 12:
        raise RuntimeError("INITIAL_ADMIN_PASSWORD deve ter pelo menos 12 caracteres.")
    if not username:
        return None
    return {
        "name": os.getenv("INITIAL_ADMIN_NAME", "Administrador").strip() or "Administrador",
        "username": username,
        "password": password,
    }
