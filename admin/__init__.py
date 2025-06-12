from flask import Blueprint

from admin import routes

admin_bp = Blueprint('admin', __name__, template_folder='templates')

admin_routes = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin',
    template_folder='templates/admin'  # 👈 tell Flask where to look
)
