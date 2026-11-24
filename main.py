#!/usr/bin/env python3
"""One Word for the Boss — entry 1.

A deterministic program that picks the single best word describing a boss
from a small local tournament, then writes exactly that one word to
/output/entry.txt.

The competition (u-swift-badger-44-one-word-for-the-boss-6b48c735) asks for
exactly one word describing the entrant's boss: no phrase, no caption, no
explanation. The gate seals /output/entry.txt as UTF-8 text of 1 to 30
characters, not only white space. The judge compares entries two at a time
on five criteria, most important first:

  1. a single word that describes a boss, the sort of word a person would
     actually use about the one they report to;
  2. funny on its own, the kind of word a colleague repeats at lunch;
  3. rings true, catching a real habit of bosses the entrant has met;
  4. fresh, not the first word anyone would reach for;
  5. travels, working for a boss in a kitchen, a warehouse or an office.

This program scores ten candidate words on those five criteria, runs a
head-to-head round robin decided by the first criterion where two words
differ, and writes the tournament winner. Everything here is fixed data
and fixed arithmetic, so every run prints the same word.

Local tournament result: "Hoverer" wins 9 of 9 duels with 23 of 25
criterion points. Runner-up "Nitpicker" takes 8 duels with 22 points,
then "Unreachable" with 7 duels and 22 points, then "Firefighter" with
6 duels and 22 points. The hover wins because the picture of a boss
drifting to your shoulder and staying there is funnier on its own than
a bleak adjective, fresher than a well-worn noun, and truer as a daily
boss habit than a crisis metaphor.
"""

import hashlib
import json
import os
import sys


BOSSWORD_GATE_MIN_CHARS = 1
BOSSWORD_GATE_MAX_CHARS = 30
BOSSWORD_JUDGE_CRITERIA = (
    "single_word_describing_a_boss",
    "funny_on_its_own",
    "rings_true_real_boss_habit",
    "fresh_surprising",
    "travels_across_industries",
)
BOSSWORD_OUTPUT_PATH = "/output/entry.txt"
BOSSWORD_TOURNAMENT_SIZE = 10
BOSSWORD_NO_DIFFERENCE = -1


def bossword_candidate_table():
    """Return the ten candidate words with their five criterion scores.

    Scores run 1 to 5 per criterion, in the judge's order. Each row was
    scored by hand against the brief: a word earns its funny mark only
    when it lands without a caption, its true mark only when it names a
    habit bosses really show, and its fresh mark only when it is not the
    first word anyone would reach for.
    """
    bossword_rows = [
        {
            "word": "Hoverer",
            "scores": [5, 4, 5, 4, 5],
            "note": "The boss who drifts to your shoulder and stays there.",
        },
        {
            "word": "Unreachable",
            "scores": [5, 4, 5, 3, 5],
            "note": "The boss who is never there when a decision is due.",
        },
        {
            "word": "Nitpicker",
            "scores": [5, 4, 5, 3, 5],
            "note": "The boss who finds the one crooked pixel in a good week.",
        },
        {
            "word": "Firefighter",
            "scores": [5, 4, 4, 4, 5],
            "note": "The boss who only appears when something is burning.",
        },
        {
            "word": "Delegator",
            "scores": [5, 3, 5, 3, 5],
            "note": "The boss whose whole job is handing you theirs.",
        },
        {
            "word": "Gatekeeper",
            "scores": [5, 3, 5, 3, 5],
            "note": "The boss every approval must pass through first.",
        },
        {
            "word": "Micromanager",
            "scores": [5, 3, 5, 2, 5],
            "note": "The boss who counts your keystrokes from two desks away.",
        },
        {
            "word": "Overlord",
            "scores": [4, 4, 3, 4, 4],
            "note": "The boss who rules the office like a small kingdom.",
        },
        {
            "word": "Taskmaster",
            "scores": [5, 2, 4, 2, 5],
            "note": "The boss who measures the day in assignments given.",
        },
        {
            "word": "Perfectionist",
            "scores": [5, 2, 4, 2, 5],
            "note": "The boss for whom finished still means not done.",
        },
    ]
    return bossword_rows


def bossword_total_score(bossword_row):
    """Add one candidate row's five criterion scores into a total."""
    bossword_total = 0
    for bossword_mark in bossword_row["scores"]:
        bossword_total += bossword_mark
    return bossword_total


def bossword_first_difference(bossword_first, bossword_second):
    """Find the first criterion index where two rows differ.

    The judge's rule is to go through the criteria in order and stop at
    the first one where the entries differ, so this helper returns that
    index. When the two rows tie on every criterion it returns the
    BOSSWORD_NO_DIFFERENCE sentinel, never a bare empty return.
    """
    for bossword_index in range(len(BOSSWORD_JUDGE_CRITERIA)):
        bossword_first_mark = bossword_first["scores"][bossword_index]
        bossword_second_mark = bossword_second["scores"][bossword_index]
        if bossword_first_mark != bossword_second_mark:
            return bossword_index
    return BOSSWORD_NO_DIFFERENCE


def bossword_duel_winner(bossword_first, bossword_second):
    """Decide one head-to-head duel between two candidate rows.

    The row with the higher mark at the first differing criterion wins.
    A full tie is broken by the higher total, then by the shorter word,
    then by the earlier row in the table, so no duel ever ends in a draw.
    """
    bossword_split = bossword_first_difference(bossword_first, bossword_second)
    if bossword_split != BOSSWORD_NO_DIFFERENCE:
        bossword_first_mark = bossword_first["scores"][bossword_split]
        bossword_second_mark = bossword_second["scores"][bossword_split]
        if bossword_first_mark > bossword_second_mark:
            return bossword_first
        return bossword_second
    bossword_first_total = bossword_total_score(bossword_first)
    bossword_second_total = bossword_total_score(bossword_second)
    if bossword_first_total != bossword_second_total:
        if bossword_first_total > bossword_second_total:
            return bossword_first
        return bossword_second
    bossword_first_len = len(bossword_first["word"])
    bossword_second_len = len(bossword_second["word"])
    if bossword_first_len != bossword_second_len:
        if bossword_first_len < bossword_second_len:
            return bossword_first
        return bossword_second
    return bossword_first


def bossword_run_round_robin(bossword_rows):
    """Run every pair once and count each row's duel wins.

    The table order is fixed, the pair order is fixed, and every duel
    has a winner, so the win counts are the same on every run.
    """
    bossword_wins = {}
    for bossword_row in bossword_rows:
        bossword_wins[bossword_row["word"]] = 0
    bossword_pair_count = len(bossword_rows)
    for bossword_i in range(bossword_pair_count):
        for bossword_j in range(bossword_i + 1, bossword_pair_count):
            bossword_champion = bossword_duel_winner(
                bossword_rows[bossword_i], bossword_rows[bossword_j]
            )
            bossword_wins[bossword_champion["word"]] += 1
    return bossword_wins


def bossword_pick_winner(bossword_rows, bossword_wins):
    """Pick the tournament winner from the round-robin win counts.

    Most duel wins takes it. A tie on wins falls back to the higher
    criterion total, then to the shorter word, then to the earlier row,
    mirroring the duel tie-breaks so the pick is fully determined.
    """
    bossword_best = None
    bossword_best_key = None
    for bossword_row in bossword_rows:
        bossword_key = (
            bossword_wins[bossword_row["word"]],
            bossword_total_score(bossword_row),
            -len(bossword_row["word"]),
        )
        if bossword_best_key is None or bossword_key > bossword_best_key:
            bossword_best = bossword_row
            bossword_best_key = bossword_key
    return bossword_best


def bossword_check_gate(bossword_word):
    """Check one word against the competition gate and report problems.

    The gate wants UTF-8 text of 1 to 30 characters, not only white
    space, and the task wants exactly one word, so a space, a newline
    or any other separator inside the word fails the check. The list
    comes back empty only when the word is safe to submit.
    """
    bossword_problems = []
    bossword_length = len(bossword_word)
    if bossword_length < BOSSWORD_GATE_MIN_CHARS:
        bossword_problems.append("word is empty")
    if bossword_length > BOSSWORD_GATE_MAX_CHARS:
        bossword_problems.append("word is longer than 30 characters")
    if bossword_word.strip() == "":
        bossword_problems.append("word is only white space")
    if any(bossword_char.isspace() for bossword_char in bossword_word):
        bossword_problems.append("word holds a space or separator")
    try:
        bossword_word.encode("utf-8")
    except UnicodeEncodeError as bossword_encode_error:
        bossword_problems.append(
            "word is not UTF-8 text: %s" % bossword_encode_error
        )
    return bossword_problems


def bossword_write_entry(bossword_word, bossword_path):
    """Write one word to the entry path, creating its folder as needed."""
    bossword_folder = os.path.dirname(bossword_path)
    if bossword_folder:
        os.makedirs(bossword_folder, exist_ok=True)
    with open(bossword_path, "w", encoding="utf-8", newline="") as bossword_file:
        bossword_file.write(bossword_word)


def bossword_build_report(bossword_rows, bossword_wins, bossword_winner):
    """Build the small JSON audit record printed on stdout."""
    bossword_ranked = sorted(
        bossword_rows,
        key=lambda bossword_row: (
            bossword_wins[bossword_row["word"]],
            bossword_total_score(bossword_row),
            -len(bossword_row["word"]),
        ),
        reverse=True,
    )
    bossword_lines = []
    for bossword_row in bossword_ranked:
        bossword_lines.append(
            {
                "word": bossword_row["word"],
                "scores": bossword_row["scores"],
                "total": bossword_total_score(bossword_row),
                "duel_wins": bossword_wins[bossword_row["word"]],
            }
        )
    bossword_digest = hashlib.sha256(
        bossword_winner["word"].encode("utf-8")
    ).hexdigest()
    bossword_report = {
        "competition": "u-swift-badger-44-one-word-for-the-boss-6b48c735",
        "entry": bossword_winner["word"],
        "entry_chars": len(bossword_winner["word"]),
        "entry_sha256": bossword_digest,
        "criteria": list(BOSSWORD_JUDGE_CRITERIA),
        "ranking": bossword_lines,
    }
    return bossword_report


def main(argv):
    """Run the tournament, gate the winner, and write the entry file."""
    bossword_rows = bossword_candidate_table()
    if len(bossword_rows) != BOSSWORD_TOURNAMENT_SIZE:
        print(
            "tournament table holds %d rows, expected %d"
            % (len(bossword_rows), BOSSWORD_TOURNAMENT_SIZE),
            file=sys.stderr,
        )
        return 2
    bossword_wins = bossword_run_round_robin(bossword_rows)
    bossword_winner = bossword_pick_winner(bossword_rows, bossword_wins)
    bossword_word = bossword_winner["word"]
    bossword_problems = bossword_check_gate(bossword_word)
    if bossword_problems:
        for bossword_problem in bossword_problems:
            print("gate problem: %s" % bossword_problem, file=sys.stderr)
        return 3
    bossword_target = BOSSWORD_OUTPUT_PATH
    if len(argv) > 1:
        bossword_target = argv[1]
    bossword_write_entry(bossword_word, bossword_target)
    bossword_report = bossword_build_report(
        bossword_rows, bossword_wins, bossword_winner
    )
    print(json.dumps(bossword_report, indent=2, sort_keys=True))
    print("wrote %s (%d chars)" % (bossword_target, len(bossword_word)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
