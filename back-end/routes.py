from flask import request, jsonify
from models import Item, db

def setup_routes(app):
    @app.route('/items', methods=['GET'])
    def get_items():
        items = Item.query.all()
        return jsonify([{"id": item.id, "name": item.name, "description": item.description} for item in items])

    @app.route('/items', methods=['POST'])
    def add_item():
        data = request.json
        new_item = Item(name=data['name'], description=data.get('description', ''))
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"message": "Item added"}), 201

    @app.route('/items/<int:item_id>', methods=['DELETE'])
    def delete_item(item_id):
        item = Item.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return jsonify({"message": "Item deleted"}), 200
        return jsonify({"error": "Item not found"}), 404
