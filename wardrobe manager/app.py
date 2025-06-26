import random
from flask import Flask, render_template, request, redirect, session, url_for, send_file, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', '127.0.0.1')  # Default to localhost
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))    # Default to port 3306
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')       # Default to root
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DATABASE', 'test')     # Default to test

app.config['UPLOAD_FOLDER'] = 'static/uploads'

print("Connecting to database with the following:")
print("Host:", os.getenv("MYSQL_HOST"))
print("User:", os.getenv("MYSQL_USER"))
print("Database:", os.getenv("MYSQL_DATABASE"))
print("Port:", os.getenv("MYSQL_PORT"))

mysql = MySQL(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Sidebar Template
sidebar = '''
<div id="sidebar" class="sidebar">
    <div class="logo-container">
       
    </div>
    <a href="javascript:void(0)" class="closebtn" onclick="closeSidebar()">×</a>
    <nav class="sidebar-nav">
        <a href="/dashboard"><span class="icon">🏠</span> Dashboard</a>
        <a href="/manage-outfits"><span class="icon">👚</span> Manage Outfits</a>
        <a href="/choose-outfit"><span class="icon">✨</span> Compose Outfit</a>
        <a href="/suggest-outfit"><span class="icon">🎲</span> Outfit Suggestions</a>
        <a href="/tryon"><span class="icon">🧥</span> Virtual Try-On</a>
        <a href="/calendar"><span class="icon">📅</span> Calendar</a>
    </nav>
    <div class="logout-container">
        <a href="/logout" class="logout"><span class="icon">🚪</span> Logout</a>
    </div>
 </div>
<div id="openSidebarButton">
    <button onclick="openSidebar()">☰</button>
</div>
<style>
body {
    margin: 0;
    font-family: 'Segoe UI', Arial, sans-serif;
    transition: background-color 0.3s;
}
#openSidebarButton {
    position: fixed;
    top: 24px;
    left: 24px;
    z-index: 1002;
}
#openSidebarButton button {
    background: linear-gradient(90deg, #60a5fa 0%, #34d399 100%);
    color: #fff;
    font-size: 22px;
    border: none;
    padding: 12px 18px;
    cursor: pointer;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(52,144,220,0.10);
    transition: background 0.2s, transform 0.2s;
}
#openSidebarButton button:hover {
    background: linear-gradient(90deg, #2563eb 0%, #059669 100%);
    transform: scale(1.05);
}
.hidden {
    display: none;
}
.sidebar {
    height: 100%;
    width: 0;
    position: fixed;
    top: 0;
    left: 0;
    background: rgba(255,255,255,0.98);
    box-shadow: 2px 0px 16px rgba(52,144,220,0.10);
    overflow-x: hidden;
    transition: 0.4s;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    padding-top: 0;
}
.sidebar .logo-container {
    text-align: center;
    margin: 32px 0 18px 0;
}
.sidebar .logo {
    width: 120px;
    height: auto;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(52,144,220,0.10);
}
.sidebar .closebtn {
    position: absolute;
    top: 18px;
    right: 28px;
    font-size: 36px;
    color: #2563eb;
    text-decoration: none;
    z-index: 1001;
    background: none;
    border: none;
    cursor: pointer;
    transition: color 0.2s;
}
.sidebar .closebtn:hover {
    color: #059669;
}
.sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 18px;
}
.sidebar-nav a {
    padding: 14px 32px 14px 32px;
    text-decoration: none;
    font-size: 1.13rem;
    color: #2563eb;
    border-radius: 10px 0 0 10px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: background 0.18s, color 0.18s, padding-left 0.18s;
    font-weight: 500;
    position: relative;
}
.sidebar-nav a .icon {
    font-size: 1.25em;
    margin-right: 6px;
}
.sidebar-nav a:hover, .sidebar-nav a:focus {
    background: linear-gradient(90deg, #e0e7ff 0%, #f0fff4 100%);
    color: #059669;
    padding-left: 40px;
}
.sidebar .logout-container {
    margin-top: auto;
    text-align: center;
    padding: 24px 0 28px 0;
}
.sidebar .logout {
    background: linear-gradient(90deg, #f87171 0%, #fbbf24 100%);
    color: #fff;
    text-align: center;
    padding: 12px 0;
    border-radius: 10px;
    text-decoration: none;
    display: block;
    font-size: 1.08rem;
    font-weight: 600;
    transition: background 0.2s, color 0.2s;
}
.sidebar .logout:hover {
    background: linear-gradient(90deg, #ef4444 0%, #f59e42 100%);
    color: #fff;
}
@media (max-width: 600px) {
    .sidebar {
        width: 0;
        min-width: 0;
        padding-top: 0;
    }
    .sidebar .logo {
        width: 80px;
    }
    .sidebar-nav a {
        font-size: 1rem;
        padding: 12px 18px 12px 18px;
    }
}
</style>
<script>
function openSidebar() {
    document.getElementById("sidebar").style.width = "270px";
    document.querySelector("body").style.backgroundColor = "rgba(0,0,0,0.08)";
    document.getElementById("openSidebarButton").classList.add("hidden");
}
function closeSidebar() {
    document.getElementById("sidebar").style.width = "0";
    document.querySelector("body").style.backgroundColor = "white";
    document.getElementById("openSidebarButton").classList.remove("hidden");
}
function toggleDropdown() {
    const dropdown = document.getElementById("profileDropdownContent");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}
window.onclick = function(event) {
    if (!event.target.matches('#profileDropdown img')) {
        const dropdown = document.getElementById("profileDropdownContent");
        if (dropdown && dropdown.style.display === "block") {
            dropdown.style.display = "none";
        }
    }
}
</script>
'''

# Routes
@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        profile_picture = request.files['profile_picture']
        profile_picture_path = None

        if profile_picture and profile_picture.filename != '':
            filename = secure_filename(profile_picture.filename)
            profile_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(profile_picture_path)

            # Save relative path for display
            profile_picture_path = f'static/uploads/{filename}'
        else:
            # Use default profile picture if none is uploaded
            profile_picture_path = 'static/images/default_profile_picture.png'

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, password, profile_picture) VALUES (%s, %s, %s)",
                        (username, password, profile_picture_path))
            mysql.connection.commit()
            cur.close()
            return redirect('/login')
        except Exception as e:
            return f"Error: {str(e)}"
    return render_template('register.html', sidebar=sidebar, container_class="container")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['profile_picture'] = user[3]  # Save the relative path to the profile picture in the session
            return redirect('/dashboard')
        else:
            return "Invalid username or password"
    return render_template('login.html', sidebar=sidebar, container_class="container")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    profile_picture = session.get('profile_picture', 'static/images/default_profile_picture.png')

    return render_template(
        'dashboard.html',
        sidebar=sidebar,
        container_class="container",
        profile_picture=profile_picture
    )

@app.route('/manage-outfits', methods=['GET', 'POST'])
def manage_outfits():
    if 'user_id' not in session:
        return redirect('/login')

    profile_picture = session.get('profile_picture', 'static/images/default_profile_picture.png')

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        if 'add_item' in request.form:
            category = request.form['category']
            item_name = request.form['item_name']
            image = request.files['image']
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)

                # Save relative path to database
                relative_path = f'uploads/{filename}'
                cur.execute("""
                    INSERT INTO outfits (user_id, category, item_name, image_path)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, category, item_name, relative_path))
                mysql.connection.commit()

        elif 'remove_item' in request.form:
            item_id = request.form['item_id']
            cur.execute("DELETE FROM outfits WHERE id = %s AND user_id = %s", (item_id, user_id))
            mysql.connection.commit()

    cur.execute("SELECT * FROM outfits WHERE user_id = %s", [user_id])
    outfits = cur.fetchall()
    cur.close()

    return render_template(
        'manage_outfits.html',
        outfits=outfits,
        sidebar=sidebar,
        container_class="container",
        profile_picture=profile_picture
    )


@app.route('/choose-outfit', methods=['GET', 'POST'])
def choose_outfit():
    if 'user_id' not in session:
        return redirect('/login')

    profile_picture = session.get('profile_picture', 'static/images/default_profile_picture.png')
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM outfits WHERE user_id = %s", [user_id])
    outfits = cur.fetchall()
    cur.close()

    shirts = [o for o in outfits if o[2] == 'Shirt']
    pants = [o for o in outfits if o[2] == 'Pants']
    shoes = [o for o in outfits if o[2] == 'Shoes']

    selected = None
    if request.method == 'POST':
        shirt_id = request.form.get('shirt')
        pant_id = request.form.get('pant')
        shoes_id = request.form.get('shoes')
        selected = {
            'shirt': next((o for o in shirts if str(o[0]) == shirt_id), None),
            'pant': next((o for o in pants if str(o[0]) == pant_id), None),
            'shoes': next((o for o in shoes if str(o[0]) == shoes_id), None)
        }

    return render_template(
        'choose_outfit.html',
        shirts=shirts,
        pants=pants,
        shoes=shoes,
        selected=selected,
        sidebar=sidebar,
        profile_picture=profile_picture
    )

@app.route('/suggest-outfit')
def suggest_outfit():
    if 'user_id' not in session:
        return redirect('/login')

    profile_picture = session.get('profile_picture', 'static/images/default_profile_picture.png')

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM outfits WHERE user_id = %s", [user_id])
    outfits = cur.fetchall()
    cur.close()

    # Randomized suggestion logic
    pants = [o for o in outfits if o[2] == 'Pants']
    shirts = [o for o in outfits if o[2] == 'Shirt']
    shoes = [o for o in outfits if o[2] == 'Shoes']

    suggestion = {
        'pants': random.choice(pants) if pants else None,
        'shirt': random.choice(shirts) if shirts else None,
        'shoes': random.choice(shoes) if shoes else None
    }

    return render_template('outfit_suggestion.html', suggestion=suggestion, sidebar=sidebar, container_class="container", profile_picture=profile_picture)

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect('/login')

    profile_picture = session.get('profile_picture', 'static/images/default_profile_picture.png')

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Fetch all items from the database
    cur.execute("SELECT * FROM outfits WHERE user_id = %s", [user_id])
    outfits = cur.fetchall()
    cur.close()

    import random

    # Filter items by category
    pants = [o for o in outfits if o[2] == 'Pants']
    shirts = [o for o in outfits if o[2] == 'Shirt']
    shoes = [o for o in outfits if o[2] == 'Shoes']

    # Create a random suggestion for each day of the week
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    weekly_outfits = []
    for day in days:
        random_pant = random.choice(pants) if pants else None
        random_shirt = random.choice(shirts) if shirts else None
        random_shoes = random.choice(shoes) if shoes else None

        weekly_outfits.append({
            'day': day,
            'pant': random_pant,
            'shirt': random_shirt,
            'shoes': random_shoes
        })

    return render_template(
        'calendar.html',
        weekly_outfits=weekly_outfits,
        profile_picture=profile_picture,
        sidebar=sidebar
    )

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('profile_picture', None)
    return redirect('/login')

@app.route('/virtual-tryon', methods=['POST'])
def virtual_tryon():
    person_url = request.form['person_url']
    cloth_url = request.form['cloth_url']

    # Отримуємо абсолютні шляхи до файлів
    person_path = person_url.replace(request.host_url + 'static/', 'static/')
    cloth_path = cloth_url.replace(request.host_url + 'static/', 'static/')

    # Якщо шляхи некоректні, скоригуйте відповідно до вашої структури!
    fastapi_url = f"http://localhost:8000/tryon?cloth_type={cloth_type}"
    files = {
        'person': open(person_path, 'rb'),
        'cloth': open(cloth_path, 'rb')
    }
    try:
        resp = requests.post(fastapi_url, files=files)
        if resp.status_code == 200:
            return resp.content, 200, {'Content-Type': 'image/png'}
        else:
            return jsonify({'error': 'FastAPI error', 'details': resp.text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/tryon', methods=['GET', 'POST'])
def tryon():
    print("POST /tryon отримано")
    print("request.files:", request.files)
    print("request.form:", request.form)
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM outfits WHERE user_id = %s", [user_id])
    outfits = cur.fetchall()
    cur.close()

    # Групуємо по категоріях
    categories = {}
    for o in outfits:
        cat = o[2]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            'id': o[0],
            'name': o[3],
            'image_path': o[4]
        })

    people = categories.get('Person', [])
    clothes = []
    for cat in categories:
        if cat != 'Person':
            for item in categories[cat]:
                item['category'] = cat
                clothes.append(item)

    result_url = None
    error = None

    if request.method == 'POST':
        person_file = request.files.get('person_upload')
        person_radio = request.form.get('person')
        cloth_file = request.files.get('cloth_upload')
        cloth_radio = request.form.get('cloth')
        cloth_type = request.form.get('cloth_type', 'upper')

        files = {}

        if person_file and person_file.filename:
            files['person'] = (person_file.filename, person_file.stream, person_file.mimetype)
        elif person_radio:
            person_path = os.path.join('static', person_radio)
            files['person'] = (os.path.basename(person_path), open(person_path, 'rb'), 'image/png')
        else:
            error = "Не вибрано фото людини!"

        if cloth_file and cloth_file.filename:
            files['cloth'] = (cloth_file.filename, cloth_file.stream, cloth_file.mimetype)
        elif cloth_radio:
            cloth_path = os.path.join('static', cloth_radio)
            files['cloth'] = (os.path.basename(cloth_path), open(cloth_path, 'rb'), 'image/png')
        else:
            error = "Не вибрано фото одягу!"

        if not error:
            fastapi_url = f"http://localhost:8000/tryon?cloth_type={cloth_type}"
            try:
                resp = requests.post(fastapi_url, files=files)
                for k, v in files.items():
                    if hasattr(v[1], 'close'):
                        try:
                            v[1].close()
                        except Exception:
                            pass
                if resp.status_code == 200:
                    result_path = os.path.join('static', 'uploads', 'result.png')
                    with open(result_path, 'wb') as f:
                        f.write(resp.content)
                    result_url = '/static/uploads/result.png'
                else:
                    error = 'Помилка FastAPI: ' + resp.text
            except Exception as e:
                error = f'Помилка з\'єднання з FastAPI: {e}'

        # Якщо AJAX-запит — повертаємо тільки блок результату
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render_template('tryon_result.html', result_url=result_url, error=error)

    return render_template(
        'tryon.html',
        people=people,
        clothes=clothes,
        categories=[c for c in categories if c != 'Person'],
        result_url=result_url,
        error=error
    )

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))  # Use the PORT environment variable or default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)

