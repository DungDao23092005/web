# File: services/inventory-service/controllers/inventory_controller.py
from flask import Blueprint, request, jsonify
# Giả định InventoryService được đặt tên là service trong pyc
from services.inventory_service import InventoryService as service 

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

# ✅ 1. CREATE ITEM (POST /api/inventory/items)
@inventory_bp.route("/items", methods=["POST"])
# [Gợi ý: Thêm @jwt_required() và @admin_required() để bảo vệ route này]
def create_item():
    data = request.get_json()
    required_fields = ["name", "part_number", "price"]

    if not data or not all(k in data for k in required_fields):
        #
        return jsonify({"error": f"Missing required fields: {', '.join(required_fields)}"}), 400

    item, error = service.create_item(data)
    if error:
        return jsonify({"error": error}), 409

    return jsonify({"message": "Item created successfully", "item": item.to_dict()}), 201

# ✅ 2. GET ALL ITEMS (GET /api/inventory/items)
@inventory_bp.route("/items", methods=["GET"])
# [Gợi ý: Thêm @jwt_required() và @admin_required()]
def get_all_items():
    #
    items = service.get_all_items()
    return jsonify([item.to_dict() for item in items]), 200

# ✅ 3. GET LOW STOCK ITEMS (GET /api/inventory/low-stock)
@inventory_bp.route("/low-stock", methods=["GET"])
# [Gợi ý: Thêm @jwt_required() và @admin_required()]
def get_low_stock():
    #
    items = service.get_low_stock_items()
    return jsonify([item.to_dict() for item in items]), 200


# ✅ 4. GET ITEM BY ID (GET /api/inventory/items/<int:item_id>)
@inventory_bp.route("/items/<int:item_id>", methods=["GET"])
# [Gợi ý: Thêm @jwt_required()]
def get_item(item_id):
    item = service.get_item_by_id(item_id)
    if not item:
        #
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item.to_dict()), 200

# ✅ 5. UPDATE ITEM (PUT /api/inventory/items/<int:item_id>)
@inventory_bp.route("/items/<int:item_id>", methods=["PUT"])
# [Gợi ý: Thêm @jwt_required() và @admin_required()]
def update_item(item_id):
    data = request.get_json()
    item, error = service.update_item(item_id, data)
    
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": "Item updated successfully", "item": item.to_dict()}), 200

# ✅ 6. DELETE ITEM (DELETE /api/inventory/items/<int:item_id>)
@inventory_bp.route("/items/<int:item_id>", methods=["DELETE"])
# [Gợi ý: Thêm @jwt_required() và @admin_required()]
def delete_item_route(item_id):
    success, message = service.delete_item(item_id)
    
    if not success:
        return jsonify({"error": message}), 404
    
    return jsonify({"message": message}), 200