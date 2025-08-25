from flask import Blueprint

orgs_bp = Blueprint('orgs', __name__)

from . import routes
