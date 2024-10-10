import datetime
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Database connection function
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='income_panel',
            user='root',
            password=''  # Leave password empty if no password set for MySQL
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Route for adding income entry
@app.route('/api/add_income', methods=['POST'])
def add_income():
    data = request.json
    
    # Validate required fields
    required_fields = ['date', 'source', 'amount', 'category', 'payment_method']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400
    
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Insert income data into the database
        query = """
            INSERT INTO income (date, source, amount, category, payment_method, transaction_id, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['date'],
            data['source'],
            data['amount'],
            data['category'],
            data['payment_method'],
            data.get('transaction_id', None),  # Optional field
            data.get('notes', None)  # Optional field
        ))
        connection.commit()
        return jsonify({"message": "Income entry added successfully"}), 201
    
    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/income', methods=['GET'])
def get_income_records():
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor(dictionary=True)

        # Base query
        query = """
            SELECT id, date, source, amount, category, payment_method, transaction_id, notes 
            FROM income
            WHERE 1 = 1
        """

        # Filtering by date range, category, and source
        params = []
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        category = request.args.get('category')
        source = request.args.get('source')

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if category:
            query += " AND category = %s"
            params.append(category)
        if source:
            query += " AND source LIKE %s"
            params.append(f"%{source}%")
        
        # Sorting (default to sorting by date)
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'ASC')  # ASC or DESC
        query += f" ORDER BY {sort_by} {sort_order}"

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        # Execute the query
        cursor.execute(query, tuple(params))
        income_records = cursor.fetchall()

        # Format data for response
        for record in income_records:
            record['amount'] = f"${record['amount']:,}"  # Format amount as currency
            if record['notes'] and len(record['notes']) > 50:
                record['notes'] = record['notes'][:50] + "..."  # Truncate long notes

        # Return paginated results
        return jsonify({
            "data": income_records,
            "pagination": {
                "page": page,
                "per_page": per_page
            }
        })

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# Expense management endpoint
@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    
    # Validate required fields
    required_fields = ['date', 'category', 'amount', 'payment_method']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400
    
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Insert expense data into the database
        query = """
            INSERT INTO expenses (date, category, amount, notes, payment_method)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['date'],
            data['category'],
            data['amount'],
            data.get('notes', None),  # Optional field
            data['payment_method']
        ))
        connection.commit()
        return jsonify({"message": "Expense entry added successfully"}), 201
    
    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()



# Route for viewing and managing expenses
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor(dictionary=True)

        # Base query
        query = """
            SELECT id, date, category, amount, notes, payment_method
            FROM expenses
            WHERE 1 = 1
        """

        # Filtering by category
        params = []
        category = request.args.get('category')
        if category:
            query += " AND category = %s"
            params.append(category)

        # Searching by amount, date, or notes
        search = request.args.get('search')
        if search:
            search_query = "%" + search + "%"
            query += " AND (amount LIKE %s OR date LIKE %s OR notes LIKE %s)"
            params.extend([search_query, search_query, search_query])

        # Sorting (default to sorting by date)
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'ASC')  # ASC or DESC
        query += f" ORDER BY {sort_by} {sort_order}"

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        # Execute the query
        cursor.execute(query, tuple(params))
        expense_records = cursor.fetchall()

        # Format data for response
        for record in expense_records:
            record['amount'] = f"${record['amount']:,}"  # Format amount as currency
            if record['notes'] and len(record['notes']) > 50:
                record['notes'] = record['notes'][:50] + "..."  # Truncate long notes

        # Return paginated results
        return jsonify({
            "data": expense_records,
            "pagination": {
                "page": page,
                "per_page": per_page
            }
        })

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Route for deleting an expense entry
@app.route('/api/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Delete query
        delete_query = "DELETE FROM expenses WHERE id = %s"
        cursor.execute(delete_query, (id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Expense not found"}), 404

        return jsonify({"message": "Expense entry deleted successfully"}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Route for editing an expense entry
@app.route('/api/expenses/<int:id>', methods=['PUT'])
def edit_expense(id):
    data = request.json
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Update query
        update_query = """
            UPDATE expenses 
            SET date = %s, category = %s, amount = %s, notes = %s, payment_method = %s
            WHERE id = %s
        """
        cursor.execute(update_query, (
            data['date'],
            data['category'],
            data['amount'],
            data.get('notes', None),
            data.get('payment_method', None),
            id
        ))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Expense not found"}), 404

        return jsonify({"message": "Expense entry updated successfully"}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()



if __name__ == '__main__':
    app.run(debug=True)
