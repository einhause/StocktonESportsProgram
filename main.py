from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import MySQLdb.cursors, re, uuid, ast, string, random
from player_calculations import *

app = Flask(__name__, static_folder="static")
app.secret_key = "secret key"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'leaguedatabase'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''  # omitted for github reupload
app.config['MAIL_PASSWORD'] = ''  # omitted for github reupload

mail = Mail(app)
mysql = MySQL(app)

account = ""

queue = []

lobby_1 = []
red_team_1 = []
blue_team_1 = []

lobby_2 = []
red_team_2 = []
blue_team_2 = []

inhouse_points = {}


# Login for Regular Users
@app.route('/', methods=['POST'])
def login():
    if request.method == 'POST' and 'summonername' in request.form:
        summonername = request.form['summonername']
        try:
            session['summoner'] = createPlayer(summonername)
            session['summonername'] = summonername
            flash('Welcome, ' + summonername + '!')
            return redirect(url_for('home'))
        except KeyError:
            flash('Invalid Summoner Name, are you registered?')
    return render_template('index.html')


# Logout for Regular Users
@app.route('/to_home')
def back_to_login():
    session.pop('summoner', None)
    session.pop('summonername', None)
    return redirect(url_for('login'))


# Login for Administrators
@app.route('/adminlogin', methods=['POST'])
def adminlogin():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin_table WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['username'] = account['username']
            return redirect(url_for('lobbysetup'))
        else:
            flash('Incorrect username/password, are you registered?')
    return render_template('adminlogin.html')


# Logout for Administrators
@app.route('/logout')
def logout():
    if 'loggedin' in session:
        session.pop('loggedin', None)
        session.pop('username', None)
    return redirect(url_for('adminlogin'))


# Code for registration of admins, currently not implemented

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST' and 'firstname' in request.form and 'lastname' in request.form and \
            'username' in request.form and 'email' in request.form and 'password' in request.form \
            and 'cpassword' in request.form:
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cpassword = request.form['cpassword']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            flash("Account already exists, please log in.")
        elif not username or not password or not email or not firstname or not lastname:
            flash('Please fill out the entire form.')
        elif not password == cpassword:
            flash('Password and confirm password fields did not match. Please try again.')
        elif not re.match(r'[\w]{4,}', username):
            flash('Username must be atleast 4 characters long and consist of only letters, numbers and underscores.')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address.')
        elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', password):
            flash('Invalid password, please follow the indicated requirements.')
        else:
            cursor.execute('INSERT INTO users (username, password, email, firstname, lastname) '
                           'VALUES ( %s, %s, %s, %s, %s)', (username, password, email, firstname, lastname,))
            mysql.connection.commit()
            flash('You have successfully registered! You may log in.')
    elif request.method == 'POST':
        flash('Please fill out the entire form.')
    return render_template('register.html')


# Forgot Username page
@app.route('/usernameforgot', methods=['POST'])
def usernameforgot():
    if 'loggedin' in session:
        return redirect(url_for('lobbysetup'))
    elif request.method == 'POST' and 'email' in request.form:
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin_table WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            # database update routine
            token = str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6)))
            cursor.execute('UPDATE admin_table SET token = %s WHERE email = %s', (token, email))
            mysql.connection.commit()
            cursor.close()

            try:
                # email routine
                email_message = Message(subject="Reset Username Request", sender='stockton.esports.rs@gmail.com',
                                        recipients=[email])
                email_message.body = render_template("resetuseremailtemplate.html", token=token, account=account)
                mail.send(email_message)
                flash('Username reset link sent, please check your inbox.')
            except:
                flash('Unable to send email, please try again.')

        else:
            flash('Could not find an account with the email address given, please try again or register.')
    elif request.method == 'POST':
        flash('Please fill out your email address.')
    return render_template('usernameforgot.html')


# Reset username page, link accessed via email sent from usernameforgot() **NOT WORKING, cant access URL**
@app.route('/usernamereset', methods=['POST'])
def usernamereset():
    if 'loggedin' in session:
        return redirect(url_for('lobbysetup'))
    elif request.method == 'POST' and 'username' in request.form and 'token' in request.form:
        username = request.form['username']
        token = request.form['token']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin_table WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            flash('Username already exists, please try a different one.')
        elif not re.match(r'[\w]{4,}', username):
            flash('Username must be atleast 4 characters long and consist of only letters, numbers and underscores.')
        elif not username:
            flash('Please fill out your username.')
        else:
            token1 = str(uuid.uuid4())
            cursor.execute('SELECT * FROM admins WHERE token = %s', (token,))
            token_exists = cursor.fetchone()
            if token_exists:
                cursor.execute(
                    'UPDATE admin_table SET token = %s, username = %s WHERE token = %s',
                    (token1, username, token))
                mysql.connection.commit()
                cursor.close()
                flash('Username successfully updated, please log in with new credentials.')
            else:
                flash('Invalid Security Code.')
    elif request.method == 'POST':
        flash('Please fill out your username.')
    return render_template('usernamereset.html')


# Password forgot page
@app.route('/passwordforgot', methods=['POST'])
def passwordforgot():
    if 'loggedin' in session:
        return redirect(url_for('lobbysetup'))
    elif request.method == 'POST' and 'email' in request.form:
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin_table WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            # database routine
            token = str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6)))
            cursor.execute('UPDATE admin_table SET token2 = %s WHERE email = %s', (token, email))
            mysql.connection.commit()
            cursor.close()
            try:
                # email routine
                email_message = Message(subject="Reset Password Request", sender='stockton.esports.rs@gmail.com',
                                        recipients=[email])
                email_message.body = render_template("resetpassemailtemplate.html", token=token, account=account)
                mail.send(email_message)
                flash('Password reset link sent, please check your inbox.')
            except:
                flash('Unable to send email, please try again.')
        else:
            flash('Could not find an account with the email address given, please try again or register.')
    elif request.method == 'POST':
        flash('Please fill out your email address.')
    return render_template('passwordforgot.html')


# Reset password page, link accessed via email sent from passwordforgot() **NOT WORKING, cant access URL**
@app.route('/passwordreset', methods=['POST'])
def passwordreset():
    if 'loggedin' in session:
        return redirect(url_for('lobbysetup'))
    elif request.method == 'POST' and 'password' in request.form and 'cpassword' in request.form and 'token' in request.form:
        password = request.form['password']
        cpassword = request.form['cpassword']
        token = request.form['token']
        if not password:
            flash('Please fill out the entire form.')
        elif not password == cpassword:
            flash('Password and confirm password fields did not match. Please try again.')
        elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', password):
            flash('Invalid password, please follow the indicated requirements.')
        else:
            token1 = str(uuid.uuid4())
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM admins WHERE token2 = %s', (token,))
            token_exists = cursor.fetchone()
            if token_exists:
                cursor.execute(
                    'UPDATE admin_table SET token2 = %s, password = %s WHERE token2 = %s',
                    (token1, password, token))
                mysql.connection.commit()
                cursor.close()
                flash('Password successfully updated, please log in with new credentials.')
            else:
                flash('Invalid Security Code.')
    elif request.method == 'POST':
        flash('Please fill out the entire form.')
    return render_template('passwordreset.html')


# Home Page, accessed by regular users
@app.route('/home')
def home():
    global queue
    if 'summonername' in session:
        return render_template('home.html', queue=queue)
    return redirect(url_for('login'))


# Joining the queue on the home page, accessed by regular users
@app.route('/join_queue/<player>', methods=['POST'])
def join_queue(player):
    global queue
    if 'summonername' in session:
        if session['summoner'] in queue:
            flash('Player already in Queue')
            return redirect(url_for('home'))
        if not player == "":
            if len(queue) < 10:
                p = createPlayer(player)
                queue.append(p)
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM inhouse_point_table WHERE summonerName = %s', (p['summonerName'],))
                acc = cursor.fetchone()
                if not acc:
                    cursor.execute('INSERT INTO inhouse_point_table (summonerName, inhouse_points) VALUES (%s, %s)',
                                   (p['summonerName'], 0))
                    inhouse_points[p['summonerName']] = 0
                    mysql.connection.commit()
                    cursor.close()
                else:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s', (p['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    inhouse_points[p['summonerName']] = points
                    mysql.connection.commit()
                    cursor.close()
                flash('Added to Queue successfully!')
                return redirect(url_for('home'))
            else:
                flash('Queue has reached capacity (10), please try again shortly.')
        else:
            flash('Invalid Player. Please input valid Summoner name on login page.')
    return redirect(url_for('login'))


# Meet the Creators Page
@app.route('/meetthecreators', methods=['GET'])
def meet_the_creators():
    return render_template('aboutthedevs.html')


# For browsing either one of the two inhouse lobbies, accessed by regular users
@app.route('/inhouse_lobby/<lobby>')
def get_inhouse_lobby(lobby):
    global lobby_1
    global lobby_2
    global red_team_1
    global red_team_2
    global blue_team_1
    global blue_team_2

    if lobby == 'lobby_2':
        on_lobby_2 = True
        return render_template('userlobby.html', lobby_2=lobby_2, red_team_2=red_team_2, blue_team_2=blue_team_2,
                               on_lobby_2=on_lobby_2)
    on_lobby_1 = True
    return render_template('userlobby.html', lobby_1=lobby_1, red_team_1=red_team_1, blue_team_1=blue_team_1,
                           on_lobby_1=on_lobby_1)


# For editing the players from the queue to either one of the lobbies, accessed by admins
@app.route('/lobbysetup/', methods=['GET'])
def lobbysetup():
    global account
    global queue
    global lobby_1
    global lobby_2

    if 'loggedin' in session:
        if not account:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM admin_table WHERE username = %s', (session['username'],))
            acc = cursor.fetchone()
            account = acc
        return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1, lobby_2=lobby_2)
    return redirect(url_for('login'))


# Moving player from queue to lobby 1 or lobby 2, accessed by admins when clicking buttons on lobbysetup(), accessed by admins
@app.route('/move_to_lobby/<player>/<lobby>')
def move_to_lobby(player, lobby):
    global account
    global queue
    global lobby_1
    global lobby_2

    pl = ast.literal_eval(player)

    if 'loggedin' in session:
        if pl in queue:
            if lobby == "lobby_1":
                if len(lobby_1) >= 10:
                    msg = "Inhouse Lobby 1 is Full (Max 10)"
                    return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                           lobby_2=lobby_2, msg=msg)
                else:
                    queue.remove(pl)
                    lobby_1.append(pl)
                    return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                           lobby_2=lobby_2)
            if lobby == "lobby_2":
                if len(lobby_2) >= 10:
                    msg = "Inhouse Lobby 2 is Full (Max 10)"
                    return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                           lobby_2=lobby_2, msg=msg)
                else:
                    queue.remove(pl)
                    lobby_2.append(pl)
                    return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                           lobby_2=lobby_2)
        else:
            return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                   lobby_2=lobby_2)
    return redirect(url_for('login'))


# Moving player from lobby_1/lobby_2 to queue, accessed by admins when clicking buttons on lobbysetup(), accessed by admins
@app.route('/remove_from_lobby/<player>/<lobby>')
def remove_from_lobby(player, lobby):
    global account
    global queue
    global lobby_1
    global lobby_2

    pl = ast.literal_eval(player)

    if 'loggedin' in session:
        if lobby == "lobby_1":
            if pl in lobby_1:
                lobby_1.remove(pl)
                queue.append(pl)
                return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                       lobby_2=lobby_2)
            else:
                return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                       lobby_2=lobby_2)
        elif lobby == "lobby_2":
            if pl in lobby_2:
                lobby_2.remove(pl)
                queue.append(pl)
                return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                       lobby_2=lobby_2)
            else:
                return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                       lobby_2=lobby_2)

        else:
            return render_template('lobbysetup.html', account=account, queue=queue, lobby_1=lobby_1,
                                   lobby_2=lobby_2)
    return redirect(url_for('login'))


# Page used for moving players from lobby to team (or vice versa), recommending players, auto-balancing, stat lookup, and
# assigning captains, accessed by admins
@app.route('/inhousesetup/<lobby>')
def inhousesetup(lobby):
    global account
    global lobby_1
    global lobby_2
    global red_team_1
    global red_team_2
    global blue_team_1
    global blue_team_2

    if 'loggedin' in session:
        if lobby == 'lobby_2':
            return render_template('inhousesetup.html', account=account, queue=queue, lobby_2=lobby_2,
                                   red_team_2=red_team_2, blue_team_2=blue_team_2, on_lobby_2=True)
        return render_template('inhousesetup.html', account=account, queue=queue, lobby_1=lobby_1,
                               red_team_1=red_team_1, blue_team_1=blue_team_1, on_lobby_1=True)
    return redirect(url_for('login'))


# Looking up stats of a player, accessed by both users (userlobby.html) and admins (inhousesetup.html)
@app.route('/stat_lookup/<player>/<lobby>')
def stat_lookup(player, lobby):
    global account
    global queue
    global lobby_1
    global lobby_2
    global red_team_1
    global blue_team_1
    global red_team_2
    global blue_team_2

    p = ast.literal_eval(player)

    # When users request summoner stats
    if lobby == 'lobbysetup1' or lobby == 'lobbysetup2':
        emblem = get_emblem_image(p['tier'])
        if lobby == 'lobbysetup1':
            return render_template('userlobby.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                   blue_team_1=blue_team_1, player_stats=PlayerInfo(p), emblem=emblem, on_lobby_1=True)
        else:
            return render_template('userlobby.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                   blue_team_2=blue_team_2, player_stats=PlayerInfo(p), emblem=emblem, on_lobby_2=True)

    # When admins request summoner stats
    elif lobby == 'lobby_1' or lobby == 'lobby_2':
        if 'loggedin' in session:
            emblem = get_emblem_image(p['tier'])
            if lobby == 'lobby_1':
                return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                       blue_team_1=blue_team_1, player_stats=PlayerInfo(p), emblem=emblem,
                                       on_lobby_1=True)
            else:
                return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                       blue_team_2=blue_team_2, player_stats=PlayerInfo(p), emblem=emblem,
                                       on_lobby_2=True)
        return redirect(url_for('login'))
    return redirect(url_for('login'))


# Moving player from lobby to team, accessed by admins
@app.route('/move_to_team/<player>/<team>/<lobby>')
def move_to_team(player, team, lobby):
    global account
    global lobby_1
    global lobby_2
    global red_team_1
    global blue_team_1
    global red_team_2
    global blue_team_2

    pl = ast.literal_eval(player)

    if 'loggedin' in session:
        if lobby == 'lobby_1':
            if team == 'RED' and pl in lobby_1 and len(red_team_1) < 5:
                lobby_1.remove(pl)
                red_team_1.append(pl)
            elif team == 'BLUE' and pl in lobby_1 and len(blue_team_1) < 5:
                lobby_1.remove(pl)
                blue_team_1.append(pl)
            else:
                msg = "Team is currently full (Max 5)"
                return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                       blue_team_1=blue_team_1, msg=msg, on_lobby_1=True)
            return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                   blue_team_1=blue_team_1, on_lobby_1=True)
        elif lobby == 'lobby_2':
            if team == 'RED' and pl in lobby_2 and len(red_team_2) < 5:
                lobby_2.remove(pl)
                red_team_2.append(pl)
            elif team == 'BLUE' and pl in lobby_2 and len(blue_team_2) < 5:
                lobby_2.remove(pl)
                blue_team_2.append(pl)
            else:
                msg = "Team is currently full (Max 5)"
                return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                       blue_team_2=blue_team_2, msg=msg, on_lobby_2=True)
            return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                   blue_team_2=blue_team_2, on_lobby_2=True)
        return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                               blue_team_1=blue_team_1, on_lobby_1=True)
    return redirect(url_for('login'))


# Moving player from team to lobby, accessed by admins
@app.route('/remove_from_team/<player>/<team>/<lobby>')
def remove_from_team(player, team, lobby):
    global account
    global lobby_1
    global lobby_2
    global red_team_1
    global blue_team_1
    global red_team_2
    global blue_team_2

    pl = ast.literal_eval(player)

    if 'loggedin' in session:
        if lobby == 'lobby_1':
            if team == 'RED' and pl in red_team_1:
                red_team_1.remove(pl)
                lobby_1.append(pl)
            elif team == 'BLUE' and pl in blue_team_1:
                blue_team_1.remove(pl)
                lobby_1.append(pl)
            return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                   blue_team_1=blue_team_1, on_lobby_1=True)
        elif lobby == 'lobby_2':
            if team == 'RED' and pl in red_team_2:
                red_team_2.remove(pl)
                lobby_2.append(pl)
            elif team == 'BLUE' and pl in blue_team_2:
                blue_team_2.remove(pl)
                lobby_2.append(pl)
            return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                   blue_team_2=blue_team_2, on_lobby_2=True)
        return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                               blue_team_1=blue_team_1, on_lobby_1=True)
    return redirect(url_for('login'))


# Recommending a player for either red or blue team, accessed by admins
@app.route('/recommend_player/<team>/<lobby>')
def recommend_player(team, lobby):
    global account
    global lobby_1
    global lobby_2
    global red_team_1
    global blue_team_1
    global red_team_2
    global blue_team_2

    if 'loggedin' in session:
        if lobby == 'lobby_1':
            if team == 'RED':
                recomm_red = RecommendPlayer(red_team_1, blue_team_1, lobby_1, 'RED')
                return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                       blue_team_1=blue_team_1, recomm_red=recomm_red, on_lobby_1=True)
            elif team == 'BLUE':
                recomm_blue = RecommendPlayer(blue_team_1, red_team_1, lobby_1, 'BLUE')
                return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                       blue_team_1=blue_team_1, recomm_blue=recomm_blue, on_lobby_1=True)
            return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                   blue_team_1=blue_team_1, on_lobby_1=True)
        elif lobby == 'lobby_2':
            if team == 'RED':
                recomm_red = RecommendPlayer(red_team_2, blue_team_2, lobby_2, 'RED')
                return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                       blue_team_2=blue_team_2, recomm_red=recomm_red, on_lobby_2=True)
            elif team == 'BLUE':
                recomm_blue = RecommendPlayer(blue_team_2, red_team_2, lobby_2, 'BLUE')
                return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                       blue_team_2=blue_team_2, recomm_blue=recomm_blue, on_lobby_2=True)
            return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                   blue_team_2=blue_team_2, on_lobby_2=True)
        return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                               blue_team_1=blue_team_1, on_lobby_1=True)
    return redirect(url_for('login'))


# Auto balancing teams function (Full Team Balance)
@app.route('/auto_balance/<lobby>')
def FullTB(lobby):
    global account
    global lobby_1
    global lobby_2
    global red_team_1
    global blue_team_1
    global red_team_2
    global blue_team_2
    if lobby == 'lobby_1':
        if len(red_team_1) + len(blue_team_1) + len(lobby_1) >= 10:
            while len(red_team_1) != 5 or len(blue_team_1) != 5:
                if len(red_team_1) > len(blue_team_1):
                    a = PlaceRecommend(blue_team_1, red_team_1, lobby_1)
                    lobby_1.remove(a)
                    blue_team_1.append(a)
                if len(red_team_1) < len(blue_team_1):
                    a = PlaceRecommend(red_team_1, blue_team_1, lobby_1)
                    lobby_1.remove(a)
                    red_team_1.append(a)
                if len(red_team_1) == len(blue_team_1) and len(red_team_1) < 5:
                    a = PlaceRecommend(blue_team_1, red_team_1, lobby_1)
                    lobby_1.remove(a)
                    blue_team_1.append(a)
            msg = "Teams successfully balanced!"
            return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                   blue_team_1=blue_team_1, msg=msg, on_lobby_1=True)
        else:
            msg = "Not Enough People Available to balance teams"
            return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                   blue_team_1=blue_team_1, msg=msg, on_lobby_1=True)
    elif lobby == 'lobby_2':
        if len(red_team_2) + len(blue_team_2) + len(lobby_2) >= 10:
            while len(red_team_2) != 5 or len(blue_team_2) != 5:
                if len(red_team_2) > len(blue_team_2):
                    a = PlaceRecommend(blue_team_2, red_team_2, lobby_2)
                    lobby_2.remove(a)
                    blue_team_2.append(a)
                if len(red_team_2) < len(blue_team_2):
                    a = PlaceRecommend(red_team_2, blue_team_2, lobby_2)
                    lobby_2.remove(a)
                    red_team_2.append(a)
                if len(red_team_2) == len(blue_team_2) and len(red_team_2) < 5:
                    a = PlaceRecommend(blue_team_2, red_team_2, lobby_2)
                    lobby_2.remove(a)
                    blue_team_2.append(a)
            msg = "Teams successfully balanced!"
            return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                   blue_team_2=blue_team_2, msg=msg, on_lobby_2=True)
        else:
            msg = "Not Enough People Available to balance teams"
            return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                   blue_team_2=blue_team_2, msg=msg, on_lobby_2=True)
    return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                           blue_team_1=blue_team_1, on_lobby_1=True)


@app.route('/endgame/<winning_team>/<lobby>', methods=['PATCH'])
def endgame(winning_team, lobby):
    global account
    global lobby_1
    global lobby_2
    global red_team_1
    global blue_team_1
    global red_team_2
    global blue_team_2
    global inhouse_points

    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if lobby == 'lobby_1':
            if winning_team == 'RED':
                for player in red_team_1:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points += 3
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] += 3
                for player in blue_team_1:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points -= 1
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] -= 1
                msg = "Red is the winning team for Inhouse Lobby 1. Inhouse points have been updated accordingly in Leaderboard"
                mysql.connection.commit()
                cursor.close()
                return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                       blue_team_1=blue_team_1, msg=msg, on_lobby_1=True)
            elif winning_team == 'BLUE':
                for player in blue_team_1:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points += 3
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] += 3
                for player in red_team_1:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points -= 1
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] -= 1
                msg = "Blue is the winning team for Inhouse Lobby 1. Inhouse points have been updated accordingly in Leaderboard"
                mysql.connection.commit()
                cursor.close()
                return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                       blue_team_1=blue_team_1, msg=msg, on_lobby_1=True)
            return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                                   blue_team_1=blue_team_1, on_lobby_1=True)
        elif lobby == 'lobby_2':
            if winning_team == 'RED':
                for player in red_team_2:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points += 3
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] += 3
                for player in blue_team_2:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points -= 1
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] -= 1
                msg = "Red is the winning team for Inhouse Lobby 2. Inhouse points have been updated accordingly in Leaderboard"
                mysql.connection.commit()
                cursor.close()
                return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                       blue_team_2=blue_team_2, msg=msg, on_lobby_2=True)
            elif winning_team == 'BLUE':
                for player in blue_team_2:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points += 3
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] += 3
                for player in red_team_2:
                    cursor.execute('SELECT * from inhouse_point_table where summonerName = %s',
                                   (player['summonerName'],))
                    pl = cursor.fetchone()
                    points = pl['inhouse_points']
                    points -= 1
                    cursor.execute(
                        'UPDATE inhouse_point_table SET inhouse_points = %s WHERE summonerName = %s',
                        (points, player['summonerName']))
                    inhouse_points[player['summonerName']] -= 1
                msg = "Blue is the winning team for Inhouse Lobby 2. Inhouse points have been updated accordingly in Leaderboard"
                mysql.connection.commit()
                cursor.close()
                return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                       blue_team_2=blue_team_2, msg=msg, on_lobby_2=True)
            return render_template('inhousesetup.html', account=account, lobby_2=lobby_2, red_team_2=red_team_2,
                                   blue_team_2=blue_team_2, on_lobby_2=True)
        return render_template('inhousesetup.html', account=account, lobby_1=lobby_1, red_team_1=red_team_1,
                               blue_team_1=blue_team_1, on_lobby_1=True)
    return redirect(url_for('login'))


@app.route('/leaderboard/<view>', methods=['GET'])
def leaderboard(view):
    global lobby_1
    global lobby_2
    global red_team_1
    global blue_team_1
    global red_team_2
    global blue_team_2
    global inhouse_points

    all_players = []

    if len(queue) > 0:
        all_players.extend(queue)
    if len(lobby_1) > 0:
        all_players.extend(lobby_1)
    if len(lobby_2) > 0:
        all_players.extend(lobby_2)
    if len(red_team_1) > 0:
        all_players.extend(red_team_1)
    if len(red_team_2) > 0:
        all_players.extend(red_team_2)
    if len(blue_team_1) > 0:
        all_players.extend(blue_team_1)
    if len(blue_team_2) > 0:
        all_players.extend(blue_team_2)

    all_players = sort_players(all_players, inhouse_points)

    emblems = {}

    for player in all_players:
        emblem = get_emblem_image(player['tier'])
        emblems[player['summonerName']] = emblem

    if view == "user_view":
        return render_template('leaderboard.html', all_players=all_players, view=view, emblems=emblems,
                               inhouse_points=inhouse_points)
    elif view == "admin_view":
        return render_template('leaderboard.html', all_players=all_players, view=view, emblems=emblems,
                               inhouse_points=inhouse_points)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
