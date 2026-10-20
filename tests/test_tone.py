import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tone import lint_text, screen_strings


def test_em_dash_fails():
    assert lint_text("You can do this — really.")


def test_long_sentence_fails():
    assert lint_text(" ".join(["word"] * 21) + ".")


def test_banned_word_fails():
    assert lint_text("This is easy.")


def test_honest_uncertainty_is_allowed():
    assert lint_text("This might help you.") == []


def test_narration_varies_length_and_brand_wording_is_scoped():
    sentence = " ".join(["word"] * 25) + "."
    assert lint_text(sentence, narration=True) == []
    assert lint_text(sentence)
    assert lint_text("This is easy.", brand="another-brand") == []
    assert lint_text("This is easy.", brand="videofactory")


def test_hedge_passes_in_pay_sentence():
    assert lint_text("Freelancers often start at $5 per hour.") == []


def test_abbreviation_does_not_split():
    assert lint_text("Source: FlexJobs, e.g. Jan-May 2026.") == []


def test_clean_text_passes():
    assert lint_text("You can start today. Pick one task.") == []


def test_other_language_skips_english_word_list():
    assert lint_text("This is easy to do.", lang="xx") == []


def test_screen_strings():
    js = "L.text(g,'hired for:',10,20); L.label(g,\"// top 4 tasks\",1,2); L.text(g,'it\\'s ok\\nnext',1,2)"
    assert screen_strings(js) == ["hired for:", "// top 4 tasks", "it's ok next"]


def test_spelled_out_money_counts_as_pay():
    assert lint_text("Freelancers often start at ten to twenty dollars an hour.") == []
    assert lint_text("It depends on experience. These are public numbers, not a promise.") == []


def test_provenance_label_on_screen_fails():
    assert lint_text("ILLUSTRATED", brand="another-brand")
    assert lint_text("Real capture")
    assert lint_text("Illustrative", brand="another-brand")
    assert lint_text("STOCK FOOTAGE")
    assert lint_text("Illustrative stock footage")
    assert lint_text("ILLUSTRATIVE / DRAWN")


def test_ordinary_sentence_with_provenance_word_passes():
    assert lint_text("An illustrated map of your folders.") == []


def test_provenance_words_in_narration_are_not_screen_labels():
    assert lint_text("This is an illustrated map of your folder.", narration=True) == []


def test_platform_ai_disclosure_is_allowed():
    assert lint_text("Voice-over made with AI.") == []
