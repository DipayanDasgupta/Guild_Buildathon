from flask import Blueprint, jsonify

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """Provides statistics for the main dashboard cards."""
    stats_data = [
        {"title": "Policies Sold", "value": "1.6Cr+", "description": "Total policies sold through platform"},
        {"title": "Advisors", "value": "5L+", "description": "Active advisors on platform"},
        {"title": "Insurers", "value": "42", "description": "Partner insurance companies"},
    ]
    return jsonify(stats_data)

@dashboard_bp.route('/quick-actions', methods=['GET'])
def get_quick_actions():
    """Provides data for the quick action cards."""
    actions_data = [
        {"title": "Get an Insurance Quote", "description": "Find the perfect insurance coverage tailored to your needs", "buttonText": "Get Quote"},
        {"title": "Become a Turtlemint Advisor", "description": "Grow your business by selling insurance, mutual funds & loans", "buttonText": "Join Now"},
        {"title": "Discover Embedded Solutions", "description": "Insurance technology for banks, e-commerce, fintech & enterprises", "buttonText": "Learn More"},
    ]
    return jsonify(actions_data)

@dashboard_bp.route('/products', methods=['GET'])
def get_products():
    """Provides a list of insurance products."""
    products_data = [
        {"title": "Health Insurance", "description": "Comprehensive health coverage for you and your family"},
        {"title": "Car Insurance", "description": "Protect your vehicle with comprehensive coverage"},
        {"title": "Bike Insurance", "description": "Two-wheeler insurance with instant quotes"},
        {"title": "Life Insurance", "description": "Secure your family's financial future"},
        {"title": "TurtlemintPro App", "description": "Trusted partner for your insurance business"},
        {"title": "Turtlefin Solutions", "description": "Embedded insurance and SaaS solutions"},
    ]
    return jsonify(products_data)
