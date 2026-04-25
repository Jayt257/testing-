"""
Tests for:
1. QuestionResult schema now includes user_answer and correct_answer
2. scoring_service.calculate_score propagates those fields
3. scoring_service.score_mcq_locally propagates those fields
4. groq_service._fallback_result propagates those fields
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.schemas.activity import QuestionResult, QuestionSubmission
from app.services import scoring_service, groq_service


# ─── helpers ─────────────────────────────────────────────────────────────────

def make_submission(qid, user_ans, correct_ans, prompt="Q?"):
    return QuestionSubmission(
        question_id=qid,
        block_type="short_answer",
        user_answer=user_ans,
        correct_answer=correct_ans,
        prompt=prompt,
    )


# ─── 1. Schema: QuestionResult has new fields ─────────────────────────────────

def test_question_result_schema():
    qr = QuestionResult(
        question_id="q1",
        correct=True,
        score=10,
        feedback="Good",
        user_answer="hello",
        correct_answer="hello",
    )
    assert qr.user_answer == "hello", "user_answer should be preserved"
    assert qr.correct_answer == "hello", "correct_answer should be preserved"
    print("✅ test_question_result_schema passed")


def test_question_result_schema_optional_none():
    """Old code that doesn't supply new fields should still work."""
    qr = QuestionResult(question_id="q2", correct=False, score=0)
    assert qr.user_answer is None
    assert qr.correct_answer is None
    print("✅ test_question_result_schema_optional_none passed")


# ─── 2. calculate_score propagates user/correct answer ───────────────────────

def test_calculate_score_propagates_answers():
    questions = [make_submission("q1", "my answer", "correct answer")]
    groq_scores = [{
        "question_id": "q1",
        "score": 10,
        "correct": True,
        "feedback": "Yes!",
        "user_answer": "my answer",
        "correct_answer": "correct answer",
    }]
    result = scoring_service.calculate_score(questions, max_xp=10, groq_scores=groq_scores)
    qr = result["question_results"][0]
    assert qr.user_answer == "my answer", f"Expected 'my answer', got {qr.user_answer}"
    assert qr.correct_answer == "correct answer"
    print("✅ test_calculate_score_propagates_answers passed")


def test_calculate_score_missing_answers_defaults_none():
    """Groq response without user_answer/correct_answer should not crash."""
    questions = [make_submission("q1", "X", "Y")]
    groq_scores = [{"question_id": "q1", "score": 5, "correct": False, "feedback": "Nope"}]
    result = scoring_service.calculate_score(questions, max_xp=10, groq_scores=groq_scores)
    qr = result["question_results"][0]
    assert qr.user_answer is None   # no crash, gracefully None
    assert qr.correct_answer is None
    print("✅ test_calculate_score_missing_answers_defaults_none passed")


# ─── 3. score_mcq_locally propagates user/correct answer ─────────────────────

def test_mcq_local_correct():
    q = make_submission("q1", "0", "0")
    result = scoring_service.score_mcq_locally([q], max_xp=10)
    qr = result["question_results"][0]
    assert qr.correct is True
    assert qr.score == 10
    assert qr.user_answer == "0", f"Expected '0', got {qr.user_answer}"
    assert qr.correct_answer == "0"
    print("✅ test_mcq_local_correct passed")


def test_mcq_local_wrong():
    q = make_submission("q1", "1", "0")
    result = scoring_service.score_mcq_locally([q], max_xp=10)
    qr = result["question_results"][0]
    assert qr.correct is False
    assert qr.score == 0
    assert qr.user_answer == "1"
    assert qr.correct_answer == "0"
    print("✅ test_mcq_local_wrong passed")


# ─── 4. _fallback_result propagates user/correct answer ──────────────────────

def test_fallback_result_propagates_answers():
    q = make_submission("q1", "apple", "apple")
    result = groq_service._fallback_result([q], max_xp=10)
    qr_dict = result["question_results"][0]
    assert qr_dict["user_answer"] == "apple", f"Got {qr_dict.get('user_answer')}"
    assert qr_dict["correct_answer"] == "apple"
    assert qr_dict["correct"] is True
    print("✅ test_fallback_result_propagates_answers passed")


def test_fallback_result_wrong_answer():
    q = make_submission("q1", "banana", "apple")
    result = groq_service._fallback_result([q], max_xp=10)
    qr_dict = result["question_results"][0]
    assert qr_dict["user_answer"] == "banana"
    assert qr_dict["correct_answer"] == "apple"
    assert qr_dict["correct"] is False
    print("✅ test_fallback_result_wrong_answer passed")


def test_fallback_result_near_correct_gets_partial_credit():
    """Even in fallback, near-wrong answers still get 30% partial credit."""
    q = make_submission("q1", "entirely wrong", "apple")
    result = groq_service._fallback_result([q], max_xp=10)
    qr_dict = result["question_results"][0]
    assert qr_dict["score"] == 3, f"Expected 3 (30%), got {qr_dict['score']}"
    print("✅ test_fallback_result_near_correct_gets_partial_credit passed")


# ─── runner ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_question_result_schema,
        test_question_result_schema_optional_none,
        test_calculate_score_propagates_answers,
        test_calculate_score_missing_answers_defaults_none,
        test_mcq_local_correct,
        test_mcq_local_wrong,
        test_fallback_result_propagates_answers,
        test_fallback_result_wrong_answer,
        test_fallback_result_near_correct_gets_partial_credit,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"❌ {t.__name__} FAILED: {e}")
            failed += 1
    print()
    print(f"{'='*50}")
    print(f"Results: {len(tests)-failed}/{len(tests)} tests passed")
    if failed:
        sys.exit(1)
