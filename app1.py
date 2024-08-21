import mysql.connector
from flask import Flask, render_template, request, session, jsonify
from flask_session import Session
import pickle
import math
from sklearn.neighbors import NearestNeighbors
import os

# Connect to MySQL database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="myntra"
)

# Initialize the Flask app
app = Flask(__name__, template_folder="D:/OneDrive/Mukta_OneDrive/Mukta_exploration/Myntra_2024/Final/Database/templates")

# Configure Flask session
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Load the pre-trained embeddings
with open('embeddings.pkl', 'rb') as f:
    df_embeddings = pickle.load(f)
    

# Fit the NearestNeighbors model
neighbors = NearestNeighbors(n_neighbors=5, algorithm='ball_tree', metric='euclidean')
neighbors.fit(df_embeddings.drop(columns=['image_path']))

# Function to find similar items
def find_similar_items(image_filename, df_embeddings, neighbors):
    # Extracting just the filenames from the full paths in the DataFrame
    df_embeddings['filename'] = df_embeddings['image_path'].apply(lambda x: os.path.basename(x))
    print("All image paths in df_embeddings:")
    print(df_embeddings['image_path'].tolist())
    
    # Debugging: Check if the filename exists in the DataFrame
    print(f"Looking for image filename: {image_filename}")
    if image_filename not in df_embeddings['filename'].values:
        print(f"Filename {image_filename} not found in the embeddings!")
        return []
    
    # Get the index of the image
    img_index = df_embeddings[df_embeddings['filename'] == image_filename].index[0]
    
    # Get similar images
    distances, indices = neighbors.kneighbors([df_embeddings.drop(columns=['image_path', 'filename']).iloc[img_index]])
    similar_images = df_embeddings.iloc[indices[0]]['image_path'].values

    # Convert the full path to a relative path starting from the 'static' directory
    similar_images_relative = [os.path.relpath(img_path, start='D:/OneDrive/Mukta_OneDrive/Mukta_exploration/Myntra_2024/Final/Database/static') for img_path in similar_images]

    return similar_images_relative

# Route to recommend similar images
@app.route('/recommend', methods=['POST'])
def recommend():
    image_id = request.form['image_id']
    print(f"Received image_id: {image_id}")
    
    similar_images = find_similar_items(image_id, df_embeddings, neighbors)
    print(f"Similar images found: {similar_images}")
    
    return jsonify(similar_images=similar_images)

# Route for login page
@app.route('/')
def login_page():
    return render_template("login.html")

# Route to handle login form submission
@app.route("/form_login", methods=["POST"])
def login():
    user = request.form["username"]
    pwd = request.form["password"]

    mycursor = mydb.cursor()
    mycursor.execute("SELECT password FROM users WHERE username=%s", (user,))
    result = mycursor.fetchone()

    if result:
        stored_pass = result[0]
        if stored_pass != pwd:
            return render_template("login.html", info="Invalid Password")
        else:
            session['username'] = user
            return render_template("home8.html")
    else:
        return render_template("login.html", info="User not found")

# Route for the home page
@app.route('/home8.html')
def home_page():
    return render_template("home8.html")

# Route for the aesthetics page
@app.route('/aesthetic')
def aesthetic_page():
    return render_template("aesthetic8.html")

# Route for the lead page
@app.route('/lead6.html')
def lead_page():
    return render_template("lead6.html")

# Route for the profile page
@app.route('/profile2.html')
def profile_page():
    mycursor = mydb.cursor()
    mycursor.execute("SELECT name FROM build_aesthetics")
    aesthetic_names = mycursor.fetchall()
    return render_template("profile2.html", aesthetic_names=aesthetic_names)

# Route for the build aesthetic page
@app.route('/trial.html')
def build_aesthetic():
    return render_template("trial.html")

# Route for the build aesthetic page
@app.route('/cart.html')
def friend_cart():
    return render_template("cart.html")


# Route for the product shirts page
@app.route('/product-shirts.html')
def product_shirts():
    return render_template('product-shirts.html')

# Route for the product pants page
@app.route('/products-pants.html')
def products_pants():
    return render_template('products-pants.html')

# Route for the pant only page
@app.route('/pant-only2.html')
def pant_only():
    return render_template('pant-only2.html')

# Route for the shirt only page
@app.route('/shirt-only1.html')
def white_shirt_chosen():
    return render_template('shirt-only1.html')


# Route for the shirt only page
@app.route('/tank.html')
def tank():
    return render_template('tank.html')

# Route to add a new aesthetic name
@app.route('/add_name', methods=["POST"])
def add_name():
    aesthetic_name = request.form["aesthetic_name"]
    
    insert_query = "INSERT INTO build_aesthetics (name) VALUES (%s)"
    
    try:
        mycursor = mydb.cursor()
        mycursor.execute(insert_query, (aesthetic_name,))
        mydb.commit()
        return render_template("trial.html", message=f"Name '{aesthetic_name}' added successfully.")
    except mysql.connector.Error as err:
        return render_template("trial.html", error=f"Error: {err}")

# Route to save selected items
@app.route('/save_items', methods=['POST'])
def save_items():
    aesthetic_name = request.form.get('aesthetic_name')
    items = request.form.get('items')
    
    if not aesthetic_name or not items:
        return 'Error: Missing data', 400
    
    items = json.loads(items)

    insert_query = "INSERT INTO selected_items (aesthetic_name, item_name) VALUES (%s, %s)"
    try:
        mycursor = mydb.cursor()
        for item in items:
            mycursor.execute(insert_query, (aesthetic_name, item))
        mydb.commit()
        return 'Success', 200
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# Route for the shared cart page
@app.route('/shared_cart.html')
def shared_cart():
    username = session.get('username')
    if not username:
        return "User not logged in", 403

    try:
        mycursor = mydb.cursor()

        query_items = """
        SELECT s.article_id, s.name, s.description, s.price, s.image, u.username as added_by
        FROM shared_cart_items s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.shared_cart_id = (
            SELECT shared_cart_id
            FROM shared_cart_users
            WHERE user_id = (
                SELECT user_id
                FROM users
                WHERE username = %s
            )
        )
        """

        mycursor.execute(query_items, (username,))
        items = mycursor.fetchall()

        query_users = """
        SELECT DISTINCT u.username
        FROM shared_cart_users sc
        JOIN users u ON sc.user_id = u.user_id
        WHERE sc.shared_cart_id = (
            SELECT shared_cart_id
            FROM shared_cart_users
            WHERE user_id = (
                SELECT user_id
                FROM users
                WHERE username = %s
            )
        )
        """

        mycursor.execute(query_users, (username,))
        users = mycursor.fetchall()
        user_list = [user[0] for user in users]

        return render_template("shared_cart.html", items=items, users=user_list)

    except mysql.connector.Error as err:
        return f"Database error: {err}", 500

# Route for the place order page
@app.route('/place_order')
def place_order():
    return render_template("paymentpage.html")

# Route for the 50-50 page
@app.route('/5050.html')
def fofo():
    username = session.get('username')
    if not username:
        return "User not logged in", 403

    mycursor = mydb.cursor()

    query_all = """
    SELECT f.article_id, f.name, f.description, f.price, f.image
    FROM fofo f
    """
    mycursor.execute(query_all)
    all_items = mycursor.fetchall()

    query_sum = """
    SELECT SUM(price) FROM fofo
    """
    mycursor.execute(query_sum)
    total_sum_result = mycursor.fetchone()
    total_sum = total_sum_result[0] if total_sum_result[0] is not None else 0

    query_user_count = """
    SELECT COUNT(DISTINCT username) FROM users
    """
    mycursor.execute(query_user_count)
    user_count_result = mycursor.fetchone()
    user_count = user_count_result[0] if user_count_result[0] is not None else 1

    amount_payable = total_sum / user_count
    amount_payable_rounded = math.ceil(amount_payable)

    return render_template("5050.html", all_items=all_items, amount_payable=amount_payable_rounded)

# Route for the one-done page
@app.route('/onedone.html')
def oad():
    username = session.get('username')
    if not username:
        return "User not logged in", 403

    mycursor = mydb.cursor()

    query_all = """
    SELECT o.article_id, o.name, o.description, o.price, o.image
    FROM oad o
    """
    mycursor.execute(query_all)
    all_items = mycursor.fetchall()

    query_sum = """
    SELECT SUM(price) FROM oad
    """
    mycursor.execute(query_sum)
    total_sum_result = mycursor.fetchone()
    total_sum = total_sum_result[0] if total_sum_result[0] is not None else 0

    amount_payable = total_sum
    amount_payable_rounded = math.ceil(amount_payable)

    return render_template("onedone.html", all_items=all_items, amount_payable=amount_payable_rounded)

# Route for the go-dutch page
@app.route('/godutch.html')
def gd():
    username = session.get('username')
    if not username:
        return "User not logged in", 403

    mycursor = mydb.cursor()

    query_all = """
    SELECT g.article_id, g.name, g.description, g.price, g.image
    FROM gd g
    """
    mycursor.execute(query_all)
    all_items = mycursor.fetchall()

    query_user = """
    SELECT g.price
    FROM gd g
    JOIN users u ON g.user_id = u.user_id
    WHERE u.username = %s
    """
    mycursor.execute(query_user, (username,))
    user_items = mycursor.fetchall()

    total_amount = sum(row[0] for row in user_items)
    amount_payable = total_amount

    return render_template("godutch.html", all_items=all_items, amount_payable=amount_payable)

@app.route('/add_to_bag', methods=['POST'])
def add_to_bag():
    username = session.get('username')
    
    if not username:
        return redirect(url_for('login_page'))

    product_name = request.form.get('product_name')
    description = request.form.get('description')
    price = request.form.get('price')
    image_path = request.form.get('image_path')

    shared_cart_id = 888
    article_id = 55  # You might want to generate this dynamically

    mycursor = mydb.cursor()
    mycursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user_id_result = mycursor.fetchone()

    if user_id_result:
        user_id = user_id_result[0]
    else:
        return render_template('tank.html', message="User not found")

    try:
        insert_query = """
            INSERT INTO shared_cart_items (article_id, shared_cart_id, user_id, name, description, price, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        mycursor.execute(insert_query, (article_id, shared_cart_id, user_id, product_name, description, price, image_path))
        mydb.commit()
        return render_template('tank.html', message="Item added to bag")
    except mysql.connector.Error as err:
        return render_template('tank.html', message=f"Already added to bag")




# Run the app
if __name__ == '__main__':
    print("Flask app is starting...")
    app.run(debug=True, port=5050, host='0.0.0.0', use_reloader=False)
    print("Flask app is running...")
