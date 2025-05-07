import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from collections import defaultdict
import base64

# Import the Streamlit gsheets connector
from streamlit_gsheets import GSheetsConnection

# Define the URL of the publicly shared Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BuT7hk6HEJyZAmftKFcWr8w--gfuTpiIe2LY4YQAWls/edit?usp=sharing"

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

# Load data from Google Sheets using the connection object
# For publicly shared sheets, you just need the URL and worksheet name.
# The connector handles the authentication for public access.
try:
    players_df = conn.read(spreadsheet=SHEET_URL, worksheet="Players", usecols=lambda x: x.lower() in ["player"])
    matches_df = conn.read(spreadsheet=SHEET_URL, worksheet="Matches")
except Exception as e:
    st.error(f"Error loading data from Google Sheets: {e}")
    st.stop()

# Load players from DataFrame
def load_players(players_df):
    if players_df is None or "Player" not in players_df.columns:
        return []
    # Ensure 'Player' column is string type before dropna
    players_df['Player'] = players_df['Player'].astype(str)
    return players_df["Player"].dropna().tolist()

# Save players to Google Sheets (Note: Writing back to a public sheet requires authentication setup not covered here)
# If you need write functionality, you will need to configure authentication
# and potentially use methods provided by streamlit-gsheets or a different library.
def save_players(players):
    st.warning("Saving players is not fully implemented for public sheets without authentication. This function will not write data back.")
    # If you configure authentication, you might use something like:
    # conn.write(df=pd.DataFrame({"Player": players}), spreadsheet=SHEET_URL, worksheet="Players")
    pass # Currently does nothing

# Load matches from DataFrame
def load_matches(matches_df):
    if matches_df is None:
        return pd.DataFrame()
    # Ensure 'id' column exists
    if "id" not in matches_df.columns:
        matches_df["id"] = [str(uuid.uuid4()) for _ in range(len(matches_df))]
    return matches_df

# Save matches to Google Sheets (Note: Writing back to a public sheet requires authentication setup not covered here)
# If you need write functionality, you will need to configure authentication
# and potentially use methods provided by streamlit-gsheets or a different library.
def save_matches(matches):
    st.warning("Saving matches is not fully implemented for public sheets without authentication. This function will not write data back.")
    # If you configure authentication, you might use something like:
    # conn.write(df=matches, spreadsheet=SHEET_URL, worksheet="Matches")
    pass # Currently does nothing


# Load Google Fonts CSS
def load_custom_font():
    font_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap');

    html, body, [class*="st-"], [class^="css"], div, p, span, label, button,
    input, select, textarea, .stTextInput, .stSelectbox {
        font-family: 'Permanent Marker', cursive !important;
    }
    </style>
    """
    st.markdown(font_css, unsafe_allow_html=True)

# Compute points and stats
def compute_stats(matches):
    stats = defaultdict(lambda: {"points": 0, "wins": 0, "games": 0, "partners": defaultdict(int)})

    if matches.empty:
        return stats

    for _, row in matches.iterrows():
        # Ensure necessary columns exist before accessing
        if not all(col in row for col in ["match_type", "team1_player1", "team2_player1", "set1_score", "winner"]):
            continue # Skip rows with missing data

        team1 = [row["team1_player1"]] if row["match_type"] == "Singles" else [row["team1_player1"], row.get("team1_player2", "")]
        team2 = [row["team2_player1"]] if row["match_type"] == "Singles" else [row["team2_player1"], row.get("team2_player2", "")]

        # Safely parse scores
        try:
            t1_score, t2_score = map(int, str(row["set1_score"]).split("-"))
        except ValueError:
            continue # Skip rows with invalid scores

        winning_team = team1 if row["winner"] == "Team 1" else team2
        losing_team = team2 if row["winner"] == "Team 1" else team1

        for player in winning_team:
            if player: # Ensure player name is not empty
                stats[player]["points"] += 3
                stats[player]["wins"] += 1
                stats[player]["games"] += max(t1_score, t2_score)
        for player in losing_team:
             if player: # Ensure player name is not empty
                stats[player]["games"] += min(t1_score, t2_score)

        if row["match_type"] == "Doubles":
            if team1[0] and team1[1]:
                stats[team1[0]]["partners"][team1[1]] += 1
                stats[team1[1]]["partners"][team1[0]] += 1
            if team2[0] and team2[1]:
                stats[team2[0]]["partners"][team2[1]] += 1
                stats[team2[1]]["partners"][team2[0]] += 1


    return stats

# Streamlit UI
load_custom_font()
st.title("Ranches Ladies Tennis Group")

# Load data into the app
players = load_players(players_df)
matches = load_matches(matches_df)


with st.sidebar:
    st.header("Manage Players")
    new_player = st.text_input("Add New Player")
    if st.button("Add Player") and new_player and new_player not in players:
        players.append(new_player)
        save_players(players) # This will show a warning as save is not fully implemented
        st.experimental_rerun()

    remove_player = st.selectbox("Remove Player", ["" ] + players)
    if st.button("Remove Selected Player") and remove_player:
        players.remove(remove_player)
        save_players(players) # This will show a warning as save is not fully implemented
        st.experimental_rerun()

    st.header("Edit/Delete Match")
    match_to_edit = st.selectbox("Select Match to Edit/Delete", matches["id"].tolist() if not matches.empty else [])
    if match_to_edit:
        if st.button("Delete Match"):
            matches = matches[matches["id"] != match_to_edit].reset_index(drop=True) # Reset index after dropping
            save_matches(matches) # This will show a warning as save is not fully implemented
            st.experimental_rerun()

st.header("Enter Match Result")
match_type = st.radio("Match Type", ["Singles", "Doubles"])
available_players = players.copy()

if match_type == "Singles":
    p1 = st.selectbox("Player 1", available_players)
    available_players = [p for p in available_players if p != p1]
    p2 = st.selectbox("Player 2", available_players)
    team1 = [p1]
    team2 = [p2]
else:
    p1 = st.selectbox("Team 1 - Player 1", available_players, key="t1p1")
    available_players = [p for p in available_players if p != p1]
    p2 = st.selectbox("Team 1 - Player 2", available_players, key="t1p2")
    available_players = [p for p in available_players if p != p2]
    p3 = st.selectbox("Team 2 - Player 1", available_players, key="t2p1")
    available_players = [p for p in available_players if p != p3]
    p4 = st.selectbox("Team 2 - Player 2", available_players, key="t2p2")
    team1 = [p1, p2]
    team2 = [p3, p4]

set_score = st.selectbox("Set Score (Team 1 - Team 2)", [
    "6-0", "6-1", "6-2", "6-3", "6-4", "7-5", "7-6",
    "0-6", "1-6", "2-6", "3-6", "4-6", "5-7", "6-7"])
winner = st.radio("Winner", ["Team 1", "Team 2"])

if st.button("Submit Match"):
    # Basic validation
    if match_type == "Singles" and (not team1[0] or not team2[0]):
        st.warning("Please select two different players for a singles match.")
    elif match_type == "Doubles" and (not team1[0] or not team1[1] or not team2[0] or not team2[1] or len(set(team1 + team2)) != 4):
         st.warning("Please select four different players for a doubles match.")
    else:
        match_id = str(uuid.uuid4())
        new_match = {
            "id": match_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "match_type": match_type,
            "team1_player1": team1[0],
            "team1_player2": team1[1] if match_type == "Doubles" and len(team1) > 1 else "",
            "team2_player1": team2[0],
            "team2_player2": team2[1] if match_type == "Doubles" and len(team2) > 1 else "",
            "set1_score": set_score,
            "winner": winner
        }
        # Use pd.concat for adding new row and reset index
        matches = pd.concat([matches, pd.DataFrame([new_match])], ignore_index=True).reset_index(drop=True)
        save_matches(matches) # This will show a warning as save is not fully implemented
        st.success("Match recorded successfully.")
        st.experimental_rerun()


st.header("Match Records")
# Display the matches DataFrame
st.dataframe(matches)

st.header("Player Rankings")
stats = compute_stats(matches)

rankings = pd.DataFrame([
    {
        "Player": player,
        "Points": data["points"],
        "Wins": data["wins"],
        "Games Won": data["games"]
    }
    for player, data in stats.items()
])

if not rankings.empty:
    rankings = rankings.sort_values(by=["Points", "Wins", "Games Won"], ascending=False).reset_index(drop=True) # Reset index for display
    st.dataframe(rankings)
else:
    st.info("No match data available to compute rankings.")


st.header("Individual Player Insights")
if players:
    selected_player = st.selectbox("Select Player", players)
    if selected_player:
        player_data = stats.get(selected_player, {"points": 0, "wins": 0, "games": 0, "partners": {}})
        st.write(f"**Points:** {player_data['points']}")
        st.write(f"**Match Wins:** {player_data['wins']}")
        st.write(f"**Games Won:** {player_data['games']}")
        if player_data["partners"]:
            # Sort partners by count descending
            partners = sorted(player_data["partners"].items(), key=lambda x: -x[1])
            st.write("**Partners Played With:**")
            for partner, count in partners:
                if partner: # Only display if partner name is not empty
                    st.write(f"- {partner}: {count} times")
            if partners and partners[0][0]: # Check if there's a best partner and their name is not empty
                 st.write(f"**Most Frequent Partner:** {partners[0][0]}")
        else:
            st.write("**No partners recorded for this player.**")
else:
    st.info("No players available. Please add players in the sidebar.")
