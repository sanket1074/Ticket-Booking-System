from flask import Flask, render_template, request
import mysql.connector
import uuid


app = Flask(__name__)

# ---------- DB CONNECTION FUNCTION ----------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",            # change if your MySQL user is different
        password="ADD_YOUR_PASSWORD",  # change this to your MySQL password
        database="event_tickets"
    )

# ---------- ROUTE: HOME + SHOW EVENTS ----------
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    # 'message' is optional (for showing success/error)
    return render_template('index.html', events=events, message=None)

# ---------- ROUTE: BOOK TICKET ----------
@app.route('/book_ticket', methods=['POST'])
def book_ticket():
    name = request.form['name']
    email = request.form['email']
    event_id = request.form['event_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check seats
    cursor.execute("SELECT total_seats, seats_booked FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()

    if not event:
        message = "Invalid event selected."
    elif event['seats_booked'] >= event['total_seats']:
        message = "No seats available for this event."
    else:
        # Increment seats_booked
        cursor.execute(
            "UPDATE events SET seats_booked = seats_booked + 1 WHERE id = %s",
            (event_id,)
        )

        # Generate unique ticket code
        ticket_code = "EVT-" + str(uuid.uuid4())[:8].upper()

        # Insert ticket
        cursor.execute(
            "INSERT INTO tickets (ticket_code, user_name, user_email, event_id) "
            "VALUES (%s, %s, %s, %s)",
            (ticket_code, name, email, event_id)
        )
        conn.commit()
        message = f"Ticket booked successfully! Your Ticket Code: {ticket_code}"

    # Reload events for page
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', events=events, message=message)

# ---------- ROUTE: VERIFY PAGE ----------
@app.route('/verify')
def verify_page():
    return render_template('verify.html', result=None)

# ---------- ROUTE: VERIFY TICKET ----------
@app.route('/verify_ticket', methods=['POST'])
def verify_ticket():
    ticket_code = request.form['ticket_code'].strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT status FROM tickets WHERE ticket_code = %s", (ticket_code,))
    ticket = cursor.fetchone()

    if not ticket:
        result = "Invalid Ticket Code."
    elif ticket['status'] == 'USED':
        result = "Ticket already used. Entry not allowed."
    elif ticket['status'] == 'CANCELLED':
        result = "Ticket is cancelled."
    else:
        # Mark ticket as USED
        cursor.execute(
            "UPDATE tickets SET status = 'USED' WHERE ticket_code = %s",
            (ticket_code,)
        )
        conn.commit()
        result = "Ticket is VALID. Entry allowed."

    cursor.close()
    conn.close()

    return render_template('verify.html', result=result)

# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True)
