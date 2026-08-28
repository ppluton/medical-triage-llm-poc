from triage_poc.split_rebuild import assign_split, normalized_question_key


def test_equivalent_questions_always_share_a_split():
    assert normalized_question_key("Question : A?") == normalized_question_key("question a")
    assert assign_split("Question : A?") == assign_split("question a")
