import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from collections import defaultdict
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Constants
SHEET_NAME = "RLTG Data"

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Define worksheets
players_sheet = client.open(SHEET_NAME).worksheet("Players")
matches_sheet = client.open(SHEET_NAME).worksheet("Matches")

# Load players from Google Sheets
def load_players():
    df = pd.DataFrame(players_sheet.get_all_records())
    if "Player" not in df.columns:
        df = pd.DataFrame(columns=["Player"])
    return df["Player"].dropna().str.upper().tolist()

# Save players to Google Sheets
def save_players(players):
    df = pd.DataFrame({"Player": players})
    df.fillna("", inplace=True)
    players_sheet.clear()
    players_sheet.update([df.columns.tolist()] + df.values.tolist())

# Load matches from Google Sheets
def load_matches():
    df = pd.DataFrame(matches_sheet.get_all_records())
    if "id" not in df.columns:
        df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    return df

# Save matches to Google Sheets
def save_matches(matches):
    df = matches.copy()
    df.fillna("", inplace=True)
    matches_sheet.clear()
    matches_sheet.update([df.columns.tolist()] + df.values.tolist())

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
#st.markdown('''
#    <style>
#    @font-face {
#    font-family: 'Offside';
#    src: url('https://fonts.gstatic.com/s/offsideregular/v13/HI_KiYMe1YgE5Rk0h6RZz5MZq3k.woff2') format('woff2');
#    font-weight: normal;
#    font-style: normal;
#}
#    html, body, [class*="st-"], [class^="css"], h1, h2, h3, h4, h5, h6, .stText, .stMarkdown {
#        font-family: 'Offside', sans-serif !important;
#    }
#    </style>
#''', unsafe_allow_html=True)

st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Offside&display=swap');

    html, body, [class*="st-"], [class^="css"], h1, h2, h3, h4, h5, h6, .stText, .stMarkdown {
        font-family: 'Offside', sans-serif !important;
    }
    </style>
''', unsafe_allow_html=True)


st.title("Ranches Ladies Tennis Group")

players = load_players()
matches = load_matches()

with st.sidebar:
    st.header("Manage Players")
    new_player = st.text_input("Add New Player").upper()
    if st.button("Add Player") and new_player and new_player not in players:
        players.append(new_player)
        save_players(players)
        st.rerun()

    remove_player = st.selectbox("Remove Player", ["" ] + players)
    if st.button("Remove Selected Player") and remove_player:
        players.remove(remove_player)
        save_players(players)
        st.rerun()

    st.header("Edit/Delete Match")
    match_display_id = matches.copy()
    match_display_id["Players"] = match_display_id.apply(
        lambda row: f"{row['team1_player1']}{' & ' + row['team1_player2'] if row['team1_player2'] else ''} vs {row['team2_player1']}{' & ' + row['team2_player2'] if row['team2_player2'] else ''}", axis=1
    ).str.upper()
    match_display_id["label"] = match_display_id.apply(lambda row: f"{row['id']} - {row['Players']} ({row['set1_score']})", axis=1)
    match_id_map = dict(zip(match_display_id["label"], match_display_id["id"]))
    match_to_edit_label = st.selectbox("Select Match to Edit/Delete", match_display_id["label"].tolist() if not matches.empty else [])
    match_to_edit = match_id_map.get(match_to_edit_label, None)
    if match_to_edit:
        match_row = matches[matches["id"] == match_to_edit].iloc[0]
        st.write("### Edit Match")
        edit_type = st.radio("Match Type", ["Singles", "Doubles"], index=0 if match_row["match_type"] == "Singles" else 1)
        editable_players = players.copy()

        if edit_type == "Singles":
            ep1 = st.selectbox("Player 1", editable_players, index=editable_players.index(match_row["team1_player1"]))
            editable_players = [p for p in editable_players if p != ep1]
            ep2 = st.selectbox("Player 2", editable_players, index=editable_players.index(match_row["team2_player1"]))
            et1 = [ep1]
            et2 = [ep2]
        else:
            ep1 = st.selectbox("Team 1 - Player 1", editable_players, index=editable_players.index(match_row["team1_player1"]), key="e1")
            editable_players = [p for p in editable_players if p != ep1]
            ep2 = st.selectbox("Team 1 - Player 2", editable_players, index=editable_players.index(match_row["team1_player2"]), key="e2")
            editable_players = [p for p in editable_players if p != ep2]
            ep3 = st.selectbox("Team 2 - Player 1", editable_players, index=editable_players.index(match_row["team2_player1"]), key="e3")
            editable_players = [p for p in editable_players if p != ep3]
            ep4 = st.selectbox("Team 2 - Player 2", editable_players, index=editable_players.index(match_row["team2_player2"]), key="e4")
            et1 = [ep1, ep2]
            et2 = [ep3, ep4]

        new_score = st.selectbox("Update Score", [
            "6-0", "6-1", "6-2", "6-3", "6-4", "7-5", "7-6",
            "0-6", "1-6", "2-6", "3-6", "4-6", "5-7", "6-7"],
            index=[
                "6-0", "6-1", "6-2", "6-3", "6-4", "7-5", "7-6",
                "0-6", "1-6", "2-6", "3-6", "4-6", "5-7", "6-7"
            ].index(match_row["set1_score"])
        )
        new_winner = st.radio("Update Winner", ["Team 1", "Team 2"],
                              index=0 if match_row["winner"] == "Team 1" else 1)
        if st.button("Update Match"):
            matches.loc[matches["id"] == match_to_edit, "match_type"] = edit_type
            matches.loc[matches["id"] == match_to_edit, "team1_player1"] = et1[0]
            matches.loc[matches["id"] == match_to_edit, "team1_player2"] = et1[1] if edit_type == "Doubles" else ""
            matches.loc[matches["id"] == match_to_edit, "team2_player1"] = et2[0]
            matches.loc[matches["id"] == match_to_edit, "team2_player2"] = et2[1] if edit_type == "Doubles" else ""
            matches.loc[matches["id"] == match_to_edit, "set1_score"] = new_score
            matches.loc[matches["id"] == match_to_edit, "winner"] = new_winner
            save_matches(matches)
            st.success("Match updated successfully.")
            st.rerun()

        if st.button("Delete Match"):
            matches = matches[matches["id"] != match_to_edit]
            save_matches(matches)
            st.rerun()

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
    match_id = str(uuid.uuid4())
    new_match = {
        "id": f"Match-{datetime.now().strftime('%y%m%d%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "match_type": match_type,
        "team1_player1": team1[0],
        "team1_player2": team1[1] if match_type == "Doubles" else "",
        "team2_player1": team2[0],
        "team2_player2": team2[1] if match_type == "Doubles" else "",
        "set1_score": set_score,
        "winner": winner
    }
    matches = pd.concat([matches, pd.DataFrame([new_match])], ignore_index=True)
    save_matches(matches)
    st.success("Match recorded successfully.")
    st.rerun()

st.header("Match Records")

# Filter by player
player_filter = st.selectbox("Filter by Player (optional)", ["All"] + players)
if not matches.empty:
    match_display = matches.copy()
    if player_filter != "All":
        match_display = match_display[
            match_display.apply(lambda row: player_filter in [row['team1_player1'], row['team1_player2'], row['team2_player1'], row['team2_player2']], axis=1)
        ]
    match_display["Players"] = match_display.apply(
        lambda row: f"{row['team1_player1']}{' & ' + row['team1_player2'] if row['team1_player2'] else ''} vs {row['team2_player1']}{' & ' + row['team2_player2'] if row['team2_player2'] else ''}", axis=1
    ).str.upper()
    match_display["Formatted Date"] = pd.to_datetime(match_display["date"]).dt.strftime("%d %b %y")
    match_display = match_display[["Formatted Date", "Players", "match_type", "set1_score", "winner", "id"]]
    match_display.columns = ["Date", "Match Players", "Match Type", "Score", "Winner", "Match ID"]
    st.dataframe(match_display.set_index('Date'))

st.header("Player Rankings")
stats = compute_stats(matches)

rankings = pd.DataFrame([
    {
        "Player": player.upper(),
        "Points": data["points"],
        "Wins": data["wins"],
        "Games Won": data["games"]
    }
    for player, data in stats.items()
])

if not rankings.empty:
    rankings = rankings.sort_values(by=["Points", "Wins", "Games Won"], ascending=False)
    rankings.reset_index(drop=True, inplace=True)
    rankings.index += 1
    rankings.index.name = "Rank"
    st.dataframe(rankings)

st.header("Individual Player Insights")
selected_player = st.selectbox("Select Player", players)
if selected_player:
    player_data = stats.get(selected_player, {"points": 0, "wins": 0, "games": 0, "partners": {}})
    st.write(f"**Points:** {player_data['points']}")
    st.write(f"**Match Wins:** {player_data['wins']}")
    st.write(f"**Games Won:** {player_data['games']}")
    st.write(f"**Matches Played:** {player_data['wins'] + sum(player_data['partners'].values())}")
    st.write(f"**Losses:** {sum(player_data['partners'].values())}")
    total_matches = player_data['wins'] + sum(player_data['partners'].values())
    win_pct = (player_data['wins'] / total_matches * 100) if total_matches else 0
    st.write(f"**Win %:** {win_pct:.1f}%")
    if player_data["partners"]:
        partners = sorted(player_data["partners"].items(), key=lambda x: -x[1])
        st.write("**Partners Played With:**")
        for partner, count in partners:
            st.write(f"- {partner.upper()}: {count} times")
        st.write(f"**Best Partner:** {partners[0][0].upper()}")
