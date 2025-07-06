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
    "1. Count how many times each asteroid has approached Earth":
        "SELECT neo_reference_id, COUNT(*) AS approach_count FROM close_approach GROUP BY neo_reference_id;",

    "2. Average velocity of each asteroid over multiple approaches":
        "SELECT neo_reference_id, AVG(relative_velocity_kmph) AS avg_velocity FROM close_approach GROUP BY neo_reference_id;",

    "3. List top 10 fastest asteroids":
        "SELECT neo_reference_id, relative_velocity_kmph FROM close_approach ORDER BY relative_velocity_kmph DESC LIMIT 10;",

    "4. Find potentially hazardous asteroids that have approached Earth more than 3 times":
        """SELECT a.name, COUNT(*) AS times_approached
           FROM asteroids a
           JOIN close_approach c ON a.id = c.neo_reference_id
           WHERE a.is_potentially_hazardous_asteroid = TRUE
           GROUP BY a.id
           HAVING times_approached > 3;""",

    "5. Find the month with the most asteroid approaches":
        "SELECT MONTH(close_approach_date) AS month, COUNT(*) AS total_approaches FROM close_approach GROUP BY MONTH(close_approach_date) ORDER BY total_approaches DESC;",

    "6. Get the asteroid with the fastest ever approach speed":
        "SELECT neo_reference_id, MAX(relative_velocity_kmph) AS max_velocity FROM close_approach;",

    "7. Sort asteroids by maximum estimated diameter (descending)":
        "SELECT name, estimated_diameter_max_km FROM asteroids ORDER BY estimated_diameter_max_km DESC;",

    "8. Asteroid whose closest approach is getting nearer over time":
        "SELECT neo_reference_id, close_approach_date, miss_distance_km FROM close_approach ORDER BY neo_reference_id, close_approach_date;",

    "9. Display name, date, and distance of each asteroid's closest approach":
        """SELECT a.name, c.close_approach_date, c.miss_distance_km
           FROM asteroids a
           JOIN close_approach c ON a.id = c.neo_reference_id
           ORDER BY c.miss_distance_km ASC;""",

    "10. Asteroids with velocity > 50,000 km/h":
        """SELECT a.name, c.relative_velocity_kmph
           FROM asteroids a
           JOIN close_approach c ON a.id = c.neo_reference_id
           WHERE c.relative_velocity_kmph > 50000;""",

    "11. Count how many approaches happened per month":
        "SELECT MONTH(close_approach_date) AS month, COUNT(*) AS count FROM close_approach GROUP BY MONTH(close_approach_date);",

    "12. Asteroid with the highest brightness (lowest magnitude)":
        "SELECT name, absolute_magnitude_h FROM asteroids ORDER BY absolute_magnitude_h ASC LIMIT 1;",

    "13. Number of hazardous vs non-hazardous asteroids":
        "SELECT is_potentially_hazardous_asteroid, COUNT(*) AS count FROM asteroids GROUP BY is_potentially_hazardous_asteroid;",

    "14. Asteroids that passed closer than the Moon (<1 LD)":
        """SELECT a.name, c.close_approach_date, c.miss_distance_lunar
           FROM asteroids a
           JOIN close_approach c ON a.id = c.neo_reference_id
           WHERE c.miss_distance_lunar < 1;""",

    "15. Asteroids that came within 0.05 AU":
        """SELECT a.name, c.close_approach_date, c.astronomical
           FROM asteroids a
           JOIN close_approach c ON a.id = c.neo_reference_id
           WHERE c.astronomical < 0.05;""",

    "16. Asteroids with multiple close approaches on different dates":
        """SELECT neo_reference_id, COUNT(DISTINCT close_approach_date) AS approach_count
           FROM close_approach
           GROUP BY neo_reference_id
           HAVING approach_count > 1
           ORDER BY approach_count DESC;""",

    "17. Average estimated diameter of hazardous asteroids":
        """SELECT AVG(estimated_diameter_min_km + estimated_diameter_max_km)/2 AS avg_diameter_km
           FROM asteroids
           WHERE is_potentially_hazardous_asteroid = TRUE;""",

    "18. Top 5 largest hazardous asteroids by max diameter":
        "SELECT name, estimated_diameter_max_km FROM asteroids WHERE is_potentially_hazardous_asteroid = TRUE ORDER BY estimated_diameter_max_km DESC LIMIT 5;",

    "19. Number of asteroid passes per orbiting body":
        "SELECT orbiting_body, COUNT(*) AS total_passes FROM close_approach GROUP BY orbiting_body ORDER BY total_passes DESC;",

    "20. Hazardous asteroids that came within 0.01 AU":
        """SELECT a.name, c.close_approach_date, c.astronomical
           FROM asteroids a
           JOIN close_approach c ON a.id = c.neo_reference_id
           WHERE c.astronomical < 0.01 AND a.is_potentially_hazardous_asteroid = TRUE;"""
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
