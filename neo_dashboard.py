import streamlit as st
import pymysql
from datetime import datetime

# ------------------ Database Connection ------------------ #
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="0223oct22",
        database="nasa",
        cursorclass=pymysql.cursors.DictCursor
    )

# ------------------ Streamlit Setup ------------------ #
st.set_page_config(page_title="NASA NEO Dashboard", layout="wide")
st.title("🚀 NASA Near-Earth Object (NEO) Tracking Dashboard")
st.markdown("Analyze asteroid approach data using filters or predefined queries.")

# ------------------ Sidebar ------------------ #
st.sidebar.header("Query Selection")
query_options = [
    "Custom Filter (All Fields)",
    "1. Count asteroid approaches",
    "2. Avg velocity per asteroid",
    "3. Top 10 fastest asteroids",
    "4. Hazardous asteroids with >3 approaches",
    "5. Month with most approaches",
    "6. Fastest approach speed",
    "7. Sort by max estimated diameter",
    "8. Closest approach trend",
    "9. Name + date + closest distance",
    "10. Asteroids > 50,000 km/h",
    "11. Monthly approach count",
    "12. Brightest asteroid (lowest mag)",
    "13. Hazardous vs Non-hazardous",
    "14. Closer than 1 LD",
    "15. Within 0.05 AU"
]
selected_query = st.sidebar.selectbox("Choose a predefined SQL query", query_options)

# ------------------ Query Map ------------------ #
sql_queries = {
    "1. Count asteroid approaches":
        "SELECT name, COUNT(*) as approach_count FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY name",
    "2. Avg velocity per asteroid":
        "SELECT name, ROUND(AVG(relative_velocity_kmph), 2) AS avg_velocity FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY name",
    "3. Top 10 fastest asteroids":
        "SELECT name, MAX(relative_velocity_kmph) AS max_velocity FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY name ORDER BY max_velocity DESC LIMIT 10",
    "4. Hazardous asteroids with >3 approaches":
        "SELECT name, COUNT(*) as approach_count FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE is_potentially_hazardous_asteroid = TRUE GROUP BY name HAVING approach_count > 3",
    "5. Month with most approaches":
        "SELECT MONTH(close_approach_date) AS month, COUNT(*) AS count FROM close_approach GROUP BY month ORDER BY count DESC LIMIT 1",
    "6. Fastest approach speed":
        "SELECT name, MAX(relative_velocity_kmph) AS max_speed FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY name ORDER BY max_speed DESC LIMIT 1",
    "7. Sort by max estimated diameter":
        "SELECT name, estimated_diameter_max_km FROM asteroids ORDER BY estimated_diameter_max_km DESC",
    "8. Closest approach trend":
        "SELECT name, close_approach_date, miss_distance_km FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY name, close_approach_date ASC",
    "9. Name + date + closest distance":
        "SELECT name, close_approach_date, miss_distance_km FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY miss_distance_km ASC",
    "10. Asteroids > 50,000 km/h":
        "SELECT name, relative_velocity_kmph FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE relative_velocity_kmph > 50000",
    "11. Monthly approach count":
        "SELECT MONTH(close_approach_date) AS month, COUNT(*) AS count FROM close_approach GROUP BY month ORDER BY month",
    "12. Brightest asteroid (lowest mag)":
        "SELECT name, MIN(absolute_magnitude_h) AS brightness FROM asteroids GROUP BY name ORDER BY brightness ASC LIMIT 1",
    "13. Hazardous vs Non-hazardous":
        "SELECT is_potentially_hazardous_asteroid, COUNT(*) as count FROM asteroids GROUP BY is_potentially_hazardous_asteroid",
    "14. Closer than 1 LD":
        "SELECT name, close_approach_date, miss_distance_lunar FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE miss_distance_lunar < 1",
    "15. Within 0.05 AU":
        "SELECT name, close_approach_date, astronomical FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE astronomical < 0.05"
}

# ------------------ Predefined Query Execution ------------------ #
if selected_query != "Custom Filter (All Fields)":
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_queries[selected_query])
                results = cursor.fetchall()
        if results:
            st.success(f" Found {len(results)} records")
            st.dataframe(results)
        else:
            st.warning("No results found.")
    except Exception as e:
        st.error(f"Error: {e}")

# ------------------ Custom Filter Section ------------------ #
else:
    st.subheader(" Custom Filter Query")
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", datetime(2025, 1, 1))
        min_velocity = st.slider("Min Relative Velocity (km/h)", 0, 100000, 0)
        min_diameter = st.slider("Min Estimated Diameter (km)", 0.0, 10.0, 0.0)

    with col2:
        end_date = st.date_input("End Date", datetime(2025, 12, 31))
        max_velocity = st.slider("Max Relative Velocity (km/h)", 1000, 200000, 100000)
        max_diameter = st.slider("Max Estimated Diameter (km)", 0.1, 20.0, 5.0)

    min_au = st.slider("Min Astronomical Distance (AU)", 0.0, 1.0, 0.0)
    max_au = st.slider("Max Astronomical Distance (AU)", 0.01, 2.0, 0.5)

    min_ld = st.slider("Min Lunar Distance (LD)", 0.0, 100.0, 0.0)
    max_ld = st.slider("Max Lunar Distance (LD)", 1.0, 500.0, 100.0)

    hazardous_state = st.selectbox("Hazardous Asteroid?", ("All", "Yes", "No"))

    if st.button(" Apply Filters"):
        query = """
            SELECT a.name, c.close_approach_date, c.relative_velocity_kmph,
                   c.miss_distance_km, c.miss_distance_lunar, c.astronomical,
                   a.estimated_diameter_min_km, a.estimated_diameter_max_km,
                   a.is_potentially_hazardous_asteroid
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.close_approach_date BETWEEN %s AND %s
              AND c.relative_velocity_kmph BETWEEN %s AND %s
              AND a.estimated_diameter_min_km >= %s
              AND a.estimated_diameter_max_km <= %s
              AND c.astronomical BETWEEN %s AND %s
              AND c.miss_distance_lunar BETWEEN %s AND %s
        """

        params = [start_date, end_date, min_velocity, max_velocity,
                  min_diameter, max_diameter, min_au, max_au, min_ld, max_ld]

        if hazardous_state == "Yes":
            query += " AND a.is_potentially_hazardous_asteroid = TRUE"
        elif hazardous_state == "No":
            query += " AND a.is_potentially_hazardous_asteroid = FALSE"

        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    filtered_results = cursor.fetchall()

            if filtered_results:
                st.success(f" Found {len(filtered_results)} records")
                st.dataframe(filtered_results)
            else:
                st.info("No asteroids found for selected filters.")
        except Exception as e:
            st.error(f"Query failed: {e}")
