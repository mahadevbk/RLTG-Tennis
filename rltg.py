import streamlit as st
import pandas as pd
import os
from datetime import datetime
from collections import defaultdict

# Load or create players.csv
if not os.path.exists("players.csv"):
    pd.DataFrame(columns=["Name"]).to_csv("players.csv", index=False)

# Load or create matches.csv
if not os.path.exists("matches.csv"):
    pd.DataFrame(columns=["Date", "Match Type", "Player 1", "Player 2", "Player 3", "Player 4", "Winner(s)", "Set Score"]).to_csv("matches.csv", index=False)

players_df = pd.read_csv("players.csv")
matches_df = pd.read_csv("matches.csv")
player_list = players_df["Name"].dropna().tolist()

st.title("🎾 Ranches Ladies Tennis Group")

# Match Entry
st.header("Enter a New Match Result")
match_type = st.selectbox("Match Type", ["Singles", "Doubles"])

if match_type == "Singles":
    p1 = st.selectbox("Player 1", player_list, key="s1")
    p2 = st.selectbox("Player 2", [p for p in player_list if p != p1], key="s2")
    winner = st.selectbox("Winner", [p1, p2], key="sw")
    score = st.text_input("Set Score (e.g., 6-3)", key="sscore")
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

elif match_type == "Doubles":
    p1 = st.selectbox("Player 1", player_list, key="d1")
    p2 = st.selectbox("Player 2", [p for p in player_list if p != p1], key="d2")
    p3 = st.selectbox("Player 3", [p for p in player_list if p not in [p1, p2]], key="d3")
    p4 = st.selectbox("Player 4", [p for p in player_list if p not in [p1, p2, p3]], key="d4")
    team1 = f"{p1} & {p2}"
    team2 = f"{p3} & {p4}"
    winner = st.selectbox("Winning Team", [team1, team2], key="dw")
    score = st.text_input("Set Score (e.g., 6-4)", key="dscore")
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

# Match Records
st.header("📜 Match Records")
st.dataframe(matches_df)

# Player Stats and Points
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
    score_split = set_score.split("-")
    try:
        games = [int(score_split[0]), int(score_split[1])]
    except:
        games = [0, 0]

    if match_type == "Singles":
        loser = row["Player 2"] if row["Winner(s)"] == row["Player 1"] else row["Player 1"]
        points[row["Winner(s)"]] += 3
        wins[row["Winner(s)"]] += 1
        games_won[row["Winner(s)"]] += games[0]
        games_won[loser] += games[1]

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
            games_won[w] += games[0]
        for l in losers:
            games_won[l] += games[1]
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

# Player-specific info
st.header("🔍 Individual Player Analysis")
selected_player = st.selectbox("Select Player", player_list)
if selected_player:
    st.subheader(f"Stats for {selected_player}")
    st.write(f"**Total Points:** {points[selected_player]}")
    st.write(f"**Match Wins:** {wins[selected_player]}")
    st.write(f"**Games Won:** {games_won[selected_player]}")

    # Partners
    if partners[selected_player]:
        partner_counts = pd.Series(partners[selected_player]).value_counts()
        best_partner = partner_counts.idxmax()
        st.write(f"**Partners Played With:** {', '.join(partner_counts.index)}")
        st.write(f"**Best Partner (Most Matches Together):** {best_partner}")
    else:
        st.write("No doubles matches yet.")

