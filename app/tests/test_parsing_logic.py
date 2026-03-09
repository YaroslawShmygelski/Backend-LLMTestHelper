import pytest

from app.parsers.google_form import (
    get_form_response_url,
    extract_script_variables,
    parse_entries,
)
from app.services.tests.tests import normalize_parsed_data
from app.schemas.tests.test import QuestionType, TestQuestions


class TestURLConversion:

    def test_viewform_replaced_to_form_response(self):
        url = "https://docs.google.com/forms/d/e/ABC123/viewform"
        result = get_form_response_url(url)
        assert result == "https://docs.google.com/forms/d/e/ABC123/formResponse"

    def test_url_without_viewform(self):
        result = get_form_response_url("https://docs.google.com/forms/d/e/ABC123")
        assert result.endswith("/formResponse")

    def test_url_with_trailing_slash(self):
        result = get_form_response_url("https://docs.google.com/forms/d/e/ABC123/")
        assert result.endswith("/formResponse")

    def test_already_form_response(self):
        url = "https://docs.google.com/forms/d/e/ABC123/formResponse"
        assert get_form_response_url(url) == url


class TestExtractScriptVariables:

    def test_extracts_json_array(self):
        html = 'var FB_PUBLIC_LOAD_DATA_ = [1, 2, "hello"];'
        assert extract_script_variables("FB_PUBLIC_LOAD_DATA_", html) == [1, 2, "hello"]

    def test_extracts_nested(self):
        html = 'var FB_PUBLIC_LOAD_DATA_ = [[1, [2, 3]], "test"];'
        assert extract_script_variables("FB_PUBLIC_LOAD_DATA_", html) == [[1, [2, 3]], "test"]

    def test_returns_none_missing(self):
        assert extract_script_variables("FB_PUBLIC_LOAD_DATA_", "<html></html>") is None

    def test_returns_none_invalid_json(self):
        assert extract_script_variables("FB_PUBLIC_LOAD_DATA_", "var FB_PUBLIC_LOAD_DATA_ = {broken};") is None


class TestParseEntries:

    def test_parses_two_questions(self, mock_form_data_structure):
        result = parse_entries(mock_form_data_structure)
        questions = [e for e in result if e["id"] not in ("pageHistory", "emailAddress")]
        assert len(questions) == 2

    def test_short_answer_fields(self, mock_form_data_structure):
        result = parse_entries(mock_form_data_structure)
        q = result[0]
        assert q["id"] == 12345
        assert q["container_name"] == "Your name"
        assert q["type"] == 0
        assert q["required"] is True
        assert q["options"] is None

    def test_multiple_choice_options(self, mock_form_data_structure):
        result = parse_entries(mock_form_data_structure)
        q = result[1]
        assert q["id"] == 67890
        assert q["type"] == 2
        assert q["options"] == ["Python", "JavaScript", "Go"]

    def test_skips_section_headers(self, mock_form_data_structure):
        result = parse_entries(mock_form_data_structure)
        assert 8 not in [e.get("type") for e in result]

    def test_page_history_added(self, mock_form_data_structure):
        result = parse_entries(mock_form_data_structure)
        pages = [e for e in result if e["id"] == "pageHistory"]
        assert len(pages) == 1
        assert pages[0]["default_value"] == "0,1"

    def test_only_required_filter(self, mock_form_data_structure):
        result = parse_entries(mock_form_data_structure, only_required=True)
        questions = [e for e in result if e["id"] not in ("pageHistory", "emailAddress")]
        assert len(questions) == 1
        assert questions[0]["required"] is True

    def test_empty_data(self):
        assert parse_entries([]) == []

    def test_none_data(self):
        assert parse_entries(None) == []


class TestNormalizeParsedData:

    def test_correct_count(self, sample_parsed_data):
        result = normalize_parsed_data(sample_parsed_data)
        assert isinstance(result, TestQuestions)
        assert len(result.questions) == 2

    def test_skips_non_integer_type(self, sample_parsed_data):
        result = normalize_parsed_data(sample_parsed_data)
        assert 999 not in [q.id for q in result.questions]

    def test_resolves_type(self, sample_parsed_data):
        result = normalize_parsed_data(sample_parsed_data)
        assert isinstance(result.questions[0].type, QuestionType)
        assert result.questions[0].type.type_id == 2

    def test_container_name_priority(self, sample_parsed_data):
        result = normalize_parsed_data(sample_parsed_data)
        assert result.questions[0].question == "What is Python?"

    def test_fallback_to_name(self):
        data = [{"id": 1, "name": "Fallback", "type": 0, "required": False}]
        assert normalize_parsed_data(data).questions[0].question == "Fallback"

    def test_preserves_options(self, sample_parsed_data):
        result = normalize_parsed_data(sample_parsed_data)
        assert result.questions[0].options == ["A language", "A snake", "Both"]

    def test_empty_list(self):
        result = normalize_parsed_data([])
        assert len(result.questions) == 0

    def test_all_google_form_types(self):
        type_ids = [0, 1, 2, 3, 4, 5, 7, 9, 10]
        data = [{"id": i, "name": f"Q{i}", "type": tid, "required": False} for i, tid in enumerate(type_ids)]
        result = normalize_parsed_data(data)
        assert len(result.questions) == 9
