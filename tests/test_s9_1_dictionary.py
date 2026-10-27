"""S9.1 (#103): the personal dictionary is applied before insert (E9, ADR-014)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

TSV = "# comment\nmiraaya\tMiraya\t23\tauto\nnavi\tNavii\t7\tauto\ncloud\tClaude\t3\task\naur ekal\taur Oracle\t2\tauto\nekal server\tOracle server\t1\tauto\nlink right\tLinkRight\t14\tauto\n"


def rules(tmp_path):
    p = tmp_path / "dictionary.tsv"; p.write_text(TSV); return d.load_dictionary(p)


def test_a_dictionary_word_is_applied(tmp_path):
    assert d.apply_dictionary("Miraaya ka kaam", rules(tmp_path)) == ("Miraya ka kaam", 1)


def test_only_whole_words(tmp_path):
    assert d.apply_dictionary("navigation aur navi", rules(tmp_path)) == ("navigation aur Navii", 1)


def test_ask_rows_are_not_swapped(tmp_path):
    assert d.apply_dictionary("cloud par", rules(tmp_path)) == ("cloud par", 0)


def test_longest_first_and_no_double_swap(tmp_path):
    assert d.apply_dictionary("aur ekal server mein", rules(tmp_path)) == ("aur Oracle server mein", 1)


def test_phrase_matches_any_case_and_spaces(tmp_path):
    assert d.apply_dictionary("Link  Right ka part", rules(tmp_path)) == ("LinkRight ka part", 1)


def test_missing_file_changes_nothing(tmp_path):
    assert d.apply_dictionary("miraaya", d.load_dictionary(tmp_path / "none.tsv")) == ("miraaya", 0)
