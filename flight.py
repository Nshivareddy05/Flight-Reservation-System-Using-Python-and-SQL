import sqlite3
import streamlit as st
import pandas as pd

# Connect to database
conn = sqlite3.connect("flight_reservation.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute("CREATE TABLE IF NOT EXISTS Passengers (passenger_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS Flights (flight_id INTEGER PRIMARY KEY AUTOINCREMENT, airline TEXT NOT NULL, origin TEXT NOT NULL, destination TEXT NOT NULL, departure_time TEXT NOT NULL, seats_available INTEGER NOT NULL, price REAL NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS Tickets (ticket_id INTEGER PRIMARY KEY AUTOINCREMENT, passenger_id INTEGER, flight_id INTEGER, status TEXT DEFAULT 'Booked', FOREIGN KEY(passenger_id) REFERENCES Passengers(passenger_id), FOREIGN KEY(flight_id) REFERENCES Flights(flight_id))")
conn.commit()

# Streamlit UI
st.title("✈️ Flight Reservation System")
menu = st.sidebar.radio("Navigation", ["Book a Flight", "Manage Flights", "Manage Tickets", "View Data"])

# --- Book a Flight ---
if menu == "Book a Flight":
    st.subheader("📌 Book a Flight Ticket")

    # Fetch available flights
    cursor.execute("SELECT * FROM Flights WHERE seats_available > 0")
    flights = cursor.fetchall()

    if flights:
        df_flights = pd.DataFrame(flights, columns=["Flight ID", "Airline", "Origin", "Destination", "Departure", "Seats", "Price"])
        st.dataframe(df_flights)

        # Booking form
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        flight_id = st.number_input("Flight ID to Book", min_value=1, step=1)

        if st.button("Book Flight"):
            cursor.execute("SELECT * FROM Flights WHERE flight_id = ? AND seats_available > 0", (flight_id,))
            selected_flight = cursor.fetchone()
            if not selected_flight:
                st.error("❌ Flight not found or no seats available.")
            elif not name or not email:
                st.warning("Please enter your name and email.")
            else:
                # Check if passenger exists
                cursor.execute("SELECT passenger_id FROM Passengers WHERE email = ?", (email,))
                passenger = cursor.fetchone()
                if passenger:
                    passenger_id = passenger[0]
                else:
                    cursor.execute("INSERT INTO Passengers (name, email) VALUES (?, ?)", (name, email))
                    passenger_id = cursor.lastrowid

                # Book ticket
                cursor.execute("INSERT INTO Tickets (passenger_id, flight_id) VALUES (?, ?)", (passenger_id, flight_id))
                cursor.execute("UPDATE Flights SET seats_available = seats_available - 1 WHERE flight_id = ?", (flight_id,))
                conn.commit()
                st.success("✅ Booking Confirmed!")

    else:
        st.info("No flights available. Please add flights first.")

# --- Manage Flights ---
elif menu == "Manage Flights":
    st.subheader("🛫 Add or Remove Flights")
    with st.form("add_flight"):
        airline = st.text_input("Airline Name")
        origin = st.text_input("Origin")
        destination = st.text_input("Destination")
        departure_time = st.text_input("Departure Time (e.g., 2025-04-20 10:30AM)")
        seats = st.number_input("Seats Available", min_value=1, step=1)
        price = st.number_input("Ticket Price", min_value=0.0, step=100.0)
        submit = st.form_submit_button("Add Flight")
        if submit:
            cursor.execute("INSERT INTO Flights (airline, origin, destination, departure_time, seats_available, price) VALUES (?, ?, ?, ?, ?, ?)",
                           (airline, origin, destination, departure_time, seats, price))
            conn.commit()
            st.success("✅ Flight added!")

    st.write("### ✈️ Current Flights")
    cursor.execute("SELECT * FROM Flights")
    all_flights = cursor.fetchall()
    if all_flights:
        df = pd.DataFrame(all_flights, columns=["Flight ID", "Airline", "Origin", "Destination", "Departure", "Seats", "Price"])
        st.dataframe(df)

# --- Manage Tickets ---
elif menu == "Manage Tickets":
    st.subheader("📃 View & Cancel Tickets")
    cursor.execute('''
        SELECT t.ticket_id, p.name, f.airline, f.origin, f.destination, t.status
        FROM Tickets t
        JOIN Passengers p ON t.passenger_id = p.passenger_id
        JOIN Flights f ON t.flight_id = f.flight_id
    ''')
    tickets = cursor.fetchall()
    if tickets:
        df = pd.DataFrame(tickets, columns=["Ticket ID", "Passenger", "Airline", "Origin", "Destination", "Status"])
        st.dataframe(df)

        cancel_id = st.number_input("Ticket ID to Cancel", min_value=1, step=1)
        if st.button("Cancel Ticket"):
            cursor.execute("UPDATE Tickets SET status = 'Cancelled' WHERE ticket_id = ?", (cancel_id,))
            cursor.execute("UPDATE Flights SET seats_available = seats_available + 1 WHERE flight_id = (SELECT flight_id FROM Tickets WHERE ticket_id = ?)", (cancel_id,))
            conn.commit()
            st.warning("❌ Ticket Cancelled")
    else:
        st.info("No tickets booked.")

# --- View Data ---
elif menu == "View Data":
    st.subheader("📊 All Data Overview")
    
    st.write("### ✈️ Flights")
    cursor.execute("SELECT * FROM Flights")
    flights = cursor.fetchall()
    if flights:
        df = pd.DataFrame(flights, columns=["Flight ID", "Airline", "Origin", "Destination", "Departure", "Seats", "Price"])
        st.dataframe(df)
    else:
        st.info("No flights in database.")

    st.write("### 🎟️ Tickets")
    cursor.execute('''
        SELECT t.ticket_id, p.name, f.airline, f.origin, f.destination, t.status
        FROM Tickets t
        JOIN Passengers p ON t.passenger_id = p.passenger_id
        JOIN Flights f ON t.flight_id = f.flight_id
    ''')
    tickets = cursor.fetchall()
    if tickets:
        df = pd.DataFrame(tickets, columns=["Ticket ID", "Passenger", "Airline", "Origin", "Destination", "Status"])
        st.dataframe(df)
    else:
        st.info("No tickets found.")
