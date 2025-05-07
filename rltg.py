import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from collections import defaultdict
import base64

# Constants
PLAYER_FILE = "players.csv"
MATCH_FILE = "matches.csv"

# Tennis scoring options
SCORE_OPTIONS = [
    "6-0", "6-1", "6-2", "6-3", "6-4", "7-5", "7-6",
    "0-6", "1-6", "2-6", "3-6", "4-6", "5-7", "6-7"
]

# Load or create player list
def load_players():
    if os.path.exists(PLAYER_FILE):
        try:
            df = pd.read_csv(PLAYER_FILE)
            if "Player" not in df.columns:
                raise ValueError("Missing 'Player' column")
            return df["Player"].dropna().tolist()
        except Exception:
            pd.DataFrame(columns=["Player"]).to_csv(PLAYER_FILE, index=False)
            return []
    else:
        pd.DataFrame(columns=["Player"]).to_csv(PLAYER_FILE, index=False)
        return []

# Save players
def save_players(players):
    pd.DataFrame({"Player": players}).to_csv(PLAYER_FILE, index=False)

# Load or create match data
def load_matches():
    if os.path.exists(MATCH_FILE):
        return pd.read_csv(MATCH_FILE)
    else:
        df = pd.DataFrame(columns=[
            "id", "date", "match_type", "team1_player1", "team1_player2",
            "team2_player1", "team2_player2", "set1_score", "winner"
        ])
        df.to_csv(MATCH_FILE, index=False)
        return df

# Save matches
def save_matches(matches):
    matches.to_csv(MATCH_FILE, index=False)

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

    for _, row in matches.iterrows():
        team1 = [row["team1_player1"]] if row["match_type"] == "Singles" else [row["team1_player1"], row["team1_player2"]]
        team2 = [row["team2_player1"]] if row["match_type"] == "Singles" else [row["team2_player1"], row["team2_player2"]]
        t1_score, t2_score = map(int, row["set1_score"].split("-"))
        winning_team = team1 if row["winner"] == "Team 1" else team2
        losing_team = team2 if row["winner"] == "Team 1" else team1

        for player in winning_team:
            stats[player]["points"] += 3
            stats[player]["wins"] += 1
            stats[player]["games"] += max(t1_score, t2_score)
        for player in losing_team:
            stats[player]["games"] += min(t1_score, t2_score)

        if row["match_type"] == "Doubles":
            stats[team1[0]]["partners"][team1[1]] += 1
            stats[team1[1]]["partners"][team1[0]] += 1
            stats[team2[0]]["partners"][team2[1]] += 1
            stats[team2[1]]["partners"][team2[0]] += 1

    return stats

# Streamlit UI
load_custom_font()
st.title("Ranches Ladies Tennis Group")

players = load_players()
matches = load_matches()

with st.sidebar:
    st.header("Manage Players")
    new_player = st.text_input("Add New Player")
    if st.button("Add Player") and new_player and new_player not in players:
        players.append(new_player)
        save_players(players)
        st.experimental_rerun()

    remove_player = st.selectbox("Remove Player", ["" ] + players)
    if st.button("Remove Selected Player") and remove_player:
        players.remove(remove_player)
        save_players(players)
        st.experimental_rerun()

    st.header("Edit/Delete Match")
    match_to_edit = st.selectbox("Select Match to Edit/Delete", matches["id"].tolist())
    if match_to_edit:
        if st.button("Delete Match"):
            matches = matches[matches["id"] != match_to_edit]
            save_matches(matches)
            st.experimental_rerun()

st.header("Enter Match Result")
match_type = st.radio("Match Type", ["Singles", "Doubles"])
available_players = players.copy()

if match_type == "Singles":
    p1 = st.selectbox("Player 1", available_players)
    available_players.remove(p1)
    p2 = st.selectbox("Player 2", available_players)
    team1 = [p1]
    team2 = [p2]
else:
    p1 = st.selectbox("Team 1 - Player 1", available_players, key="t1p1")
    available_players.remove(p1)
    p2 = st.selectbox("Team 1 - Player 2", available_players, key="t1p2")
    available_players.remove(p2)
    p3 = st.selectbox("Team 2 - Player 1", available_players, key="t2p1")
    available_players.remove(p3)
    p4 = st.selectbox("Team 2 - Player 2", available_players, key="t2p2")
    team1 = [p1, p2]
    team2 = [p3, p4]

set_score = st.selectbox("Set Score (Team 1 - Team 2)", SCORE_OPTIONS)
winner = st.radio("Winner", ["Team 1", "Team 2"])

if st.button("Submit Match"):
    match_id = str(uuid.uuid4())
    new_match = {
        "id": match_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "match_type": match_type,
        "team1_player1": team1[0],
        "team1_player2": team1[1] if match_type == "Doubles" else "",
        "team2_player1": team2[0],
        "team2_player2": team2[1] if match_type == "Doubles" else "",
        "set1_score": set_score,
        "winner": winner
    }
    matches = matches.append(new_match, ignore_index=True)
    save_matches(matches)
    st.success("Match recorded successfully.")
    st.experimental_rerun()

st.header("Match Records")
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

rankings = rankings.sort_values(by=["Points", "Wins", "Games Won"], ascending=False)
st.dataframe(rankings.reset_index(drop=True))

st.header("Individual Player Insights")
selected_player = st.selectbox("Select Player", players)
if selected_player:
    player_data = stats.get(selected_player, {"points": 0, "wins": 0, "games": 0, "partners": {}})
    st.write(f"**Points:** {player_data['points']}")
    st.write(f"**Match Wins:** {player_data['wins']}")
    st.write(f"**Games Won:** {player_data['games']}")
    if player_data["partners"]:
        partners = sorted(player_data["partners"].items(), key=lambda x: -x[1])
        st.write("**Partners Played With:**")
        for partner, count in partners:
            st.write(f"- {partner}: {count} times")
        st.write(f"**Best Partner:** {partners[0][0]}")
