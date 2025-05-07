import streamlit as st
import pandas as pd
import os
from datetime import datetime
from collections import defaultdict
import base64

# --- Load Custom Font Globally ---
def load_custom_font():
    font_path = "fonts/PermanentMarker-Regular.ttf"
    with open(font_path, "rb") as f:
        font_data = f.read()
        base64_encoded = base64.b64encode(font_data).decode()

    font_css = f"""
    <style>
    @font-face {{
        font-family: 'PermanentMarker';
        src: url(data:font/ttf;base64,{base64_encoded}) format('truetype');
    }}
    html, body, [class*="css"] {{
        font-family: 'PermanentMarker', cursive !important;
    }}
    </style>
    """
    st.markdown(font_css, unsafe_allow_html=True)

load_custom_font()

# --- File Setup ---
if not os.path.exists("players.csv"):
    pd.DataFrame(columns=["Name"]).to_csv("players.csv", index=False)
if not os.path.exists("matches.csv"):
    pd.DataFrame(columns=["Date", "Match Type", "Player 1", "Player 2", "Player 3", "Player 4", "Winner(s)", "Set Score"]).to_csv("matches.csv", index=False)

players_df = pd.read_csv("players.csv")
matches_df = pd.read_csv("matches.csv")
player_list = players_df["Name"].dropna().tolist()

# --- Valid Tennis Set Scores ---
valid_scores = [
    "6-0", "6-1", "6-2", "6-3", "6-4", "7-5", "7-6",
    "0-6", "1-6", "2-6", "3-6", "4-6", "5-7", "6-7"
]

st.title("🎾 Ranches Ladies Tennis Group")

# --- Match Entry Section ---
st.header("Enter a New Match Result")
match_type = st.selectbox("Match Type", ["Singles", "Doubles"])

if match_type == "Singles":
    p1 = st.selectbox("Player 1", player_list, key="s1")
    p2_options = [p for p in player_list if p != p1]
    p2 = st.selectbox("Player 2", p2_options, key="s2")
    winner = st.selectbox("Winner", [p1, p2], key="sw")
    score = st.selectbox("Set Score", valid_scores, key="sscore")

    if st.button("Submit Singles Match"):
        matches_df = pd.concat([matches_df, pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Match Type": "Singles",
            "Player 1": p1,
            "Player 2": p2,
            "Player 3": "",
            "Player 4": "",
            "Winner(s)": winner,
            "Set Score": score
        }])], ignore_index=True)
        matches_df.to_csv("matches.csv", index=False)
        st.success("Match recorded.")
        st.experimental_rerun()

elif match_type == "Doubles":
    p1 = st.selectbox("Player 1", player_list, key="d1")
    p2 = st.selectbox("Player 2", [p for p in player_list if p != p1], key="d2")
    p3 = st.selectbox("Player 3", [p for p in player_list if p not in [p1, p2]], key="d3")
    p4 = st.selectbox("Player 4", [p for p in player_list if p not in [p1, p2, p3]], key="d4")

    team1 = f"{p1} & {p2}"
    team2 = f"{p3} & {p4}"
    winner = st.selectbox("Winning Team", [team1, team2], key="dw")
    score = st.selectbox("Set Score", valid_scores, key="dscore")

    if st.button("Submit Doubles Match"):
        matches_df = pd.concat([matches_df, pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Match Type": "Doubles",
            "Player 1": p1,
            "Player 2": p2,
            "Player 3": p3,
            "Player 4": p4,
            "Winner(s)": winner,
            "Set Score": score
        }])], ignore_index=True)
        matches_df.to_csv("matches.csv", index=False)
        st.success("Match recorded.")
        st.experimental_rerun()

# --- Match Records Display ---
st.header("📜 Match Records")
st.dataframe(matches_df)

# --- Rankings & Stats ---
st.header("📊 Player Rankings & Stats")
points = defaultdict(int)
wins = defaultdict(int)
games_won = defaultdict(int)
partners = defaultdict(list)

for _, row in matches_df.iterrows():
    players = [row["Player 1"], row["Player 2"], row["Player 3"], row["Player 4"]]
    players = [p for p in players if p]
    match_type = row["Match Type"]
    set_score = row["Set Score"]
    try:
        g1, g2 = map(int, set_score.strip().split("-"))
    except:
        g1, g2 = 0, 0

    if match_type == "Singles":
        winner = row["Winner(s)"]
        loser = row["Player 2"] if winner == row["Player 1"] else row["Player 1"]
        points[winner] += 3
        wins[winner] += 1
        games_won[winner] += g1
        games_won[loser] += g2

    elif match_type == "Doubles":
        team1 = [row["Player 1"], row["Player 2"]]
        team2 = [row["Player 3"], row["Player 4"]]
        if row["Winner(s)"] == f"{row['Player 1']} & {row['Player 2']}":
            winners = team1
            losers = team2
        else:
            winners = team2
            losers = team1
        for w in winners:
            points[w] += 3
            wins[w] += 1
            games_won[w] += g1
        for l in losers:
            games_won[l] += g2
        for p in team1:
            partners[p].append(team1[1] if p == team1[0] else team1[0])
        for p in team2:
            partners[p].append(team2[1] if p == team2[0] else team2[0])

ranking_df = pd.DataFrame({
    "Player": list(points.keys()),
    "Points": [points[p] for p in points],
    "Wins": [wins[p] for p in points],
    "Games Won": [games_won[p] for p in points]
}).sort_values(by=["Points", "Wins", "Games Won"], ascending=False)

st.dataframe(ranking_df)

# --- Player Analysis ---
st.header("🔍 Individual Player Analysis")
selected_player = st.selectbox("Select Player", player_list)
if selected_player:
    st.subheader(f"Stats for {selected_player}")
    st.write(f"**Total Points:** {points[selected_player]}")
    st.write(f"**Match Wins:** {wins[selected_player]}")
    st.write(f"**Games Won:** {games_won[selected_player]}")
    if partners[selected_player]:
        partner_counts = pd.Series(partners[selected_player]).value_counts()
        best_partner = partner_counts.idxmax()
        st.write(f"**Partners Played With:** {', '.join(partner_counts.index)}")
        st.write(f"**Best Partner (Most Matches Together):** {best_partner}")
    else:
        st.write("No doubles matches yet.")

# --- SIDEBAR: Admin Controls ---
st.sidebar.title("⚙️ Admin Controls")

# Add Player
st.sidebar.subheader("Add a New Player")
new_player = st.sidebar.text_input("Enter player name")
if st.sidebar.button("Add Player"):
    if new_player and new_player not in player_list:
        players_df = pd.concat([players_df, pd.DataFrame([{"Name": new_player}])], ignore_index=True)
        players_df.to_csv("players.csv", index=False)
        st.sidebar.success(f"Player '{new_player}' added.")
        st.experimental_rerun()
    else:
        st.sidebar.error("Invalid or duplicate player name.")

# Remove Player
st.sidebar.subheader("Remove a Player")
remove_player = st.sidebar.selectbox("Select player to remove", player_list)
if st.sidebar.button("Remove Player"):
    players_df = players_df[players_df["Name"] != remove_player]
    players_df.to_csv("players.csv", index=False)
    st.sidebar.success(f"Player '{remove_player}' removed.")
    st.experimental_rerun()

# Edit/Delete Match
st.sidebar.subheader("Edit/Delete Match")
if not matches_df.empty:
    matches_df_display = matches_df.copy()
    matches_df_display["Match ID"] = matches_df_display.index
    match_id = st.sidebar.selectbox("Select Match to Edit/Delete", matches_df_display["Match ID"])
    match_row = matches_df_display[matches_df_display["Match ID"] == match_id].iloc[0]

    edit_type = st.sidebar.selectbox("Match Type", ["Singles", "Doubles"], index=["Singles", "Doubles"].index(match_row["Match Type"]))

    if edit_type == "Singles":
        ep1 = st.sidebar.selectbox("Player 1", player_list, index=player_list.index(match_row["Player 1"]), key="ep1")
        ep2 = st.sidebar.selectbox("Player 2", [p for p in player_list if p != ep1], index=0, key="ep2")
        ewinner = st.sidebar.selectbox("Winner", [ep1, ep2], index=0 if match_row["Winner(s)"] == ep1 else 1)
        escore = st.sidebar.selectbox("Set Score", valid_scores, index=valid_scores.index(match_row["Set Score"]) if match_row["Set Score"] in valid_scores else 0)
        ep3, ep4 = "", ""

    else:  # Doubles
        ep1 = st.sidebar.selectbox("Player 1", player_list, index=player_list.index(match_row["Player 1"]), key="epd1")
        ep2 = st.sidebar.selectbox("Player 2", [p for p in player_list if p != ep1], index=0, key="epd2")
        ep3 = st.sidebar.selectbox("Player 3", [p for p in player_list if p not in [ep1, ep2]], index=0, key="epd3")
        ep4 = st.sidebar.selectbox("Player 4", [p for p in player_list if p not in [ep1, ep2, ep3]], index=0, key="epd4")
        team1 = f"{ep1} & {ep2}"
        team2 = f"{ep3} & {ep4}"
        ewinner = st.sidebar.selectbox("Winner", [team1, team2], index=0 if match_row["Winner(s)"] == team1 else 1)
        escore = st.sidebar.selectbox("Set Score", valid_scores, index=valid_scores.index(match_row["Set Score"]) if match_row["Set Score"] in valid_scores else 0)

    if st.sidebar.button("Save Changes"):
        matches_df.at[match_id, "Match Type"] = edit_type
        matches_df.at[match_id, "Player 1"] = ep1
        matches_df.at[match_id, "Player 2"] = ep2
        matches_df.at[match_id, "Player 3"] = ep3
        matches_df.at[match_id, "Player 4"] = ep4
        matches_df.at[match_id, "Winner(s)"] = ewinner
        matches_df.at[match_id, "Set Score"] = escore
        matches_df.to_csv("matches.csv", index=False)
        st.sidebar.success("Match updated.")
        st.experimental_rerun()

    if st.sidebar.button("Delete Match"):
        matches_df = matches_df.drop(match_id)
        matches_df.to_csv("matches.csv", index=False)
        st.sidebar.success("Match deleted.")
        st.experimental_rerun()
else:
    st.sidebar.info("No matches to edit.")
