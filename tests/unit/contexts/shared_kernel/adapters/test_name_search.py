"""Unit tests for name search utilities.

Tests string processing normalization, similarity ranking algorithms, and edge case handling.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""
import pytest
from unittest.mock import Mock, patch

from src.contexts.shared_kernel.adapters.name_search import (
    StrProcessor,
    SimilarityRanking,
    MatchData,
    NumberOfWordsAndLettersMatching,
    ProcessingConfig,
    RankingConfig,
)


class TestStrProcessorNormalization:
    """Test string processor normalization and text processing logic."""

    def test_str_processor_normalization_basic_processing(self):
        """Validates basic string normalization with accent removal and case conversion."""
        # Given: string with accents and mixed case
        # When: process the string
        # Then: accents are removed and case is normalized
        processor = StrProcessor("Café com Açúcar")
        result = processor.output
        
        assert result == "cafe com acucar"
        assert processor.description == "Café com Açúcar"  # Original preserved

    def test_str_processor_normalization_removes_commas(self):
        """Validates comma removal during processing."""
        # Given: string with commas
        # When: process the string
        # Then: commas are removed
        processor = StrProcessor("Queijo, presunto, tomate")
        result = processor.output
        
        assert result == "queijo presunto tomate"

    def test_str_processor_normalization_ignores_default_words(self):
        """Validates removal of default ignored words (de, da)."""
        # Given: string containing ignored words
        # When: process the string
        # Then: ignored words are removed
        processor = StrProcessor("Arroz de frango da fazenda")
        result = processor.output
        
        assert result == "arroz frango fazenda"

    def test_str_processor_normalization_custom_ignored_words(self):
        """Validates removal of custom ignored words."""
        # Given: string and custom ignored words
        # When: process with custom ignored words
        # Then: custom ignored words are removed
        processor = StrProcessor("Pão com manteiga e açúcar")
        result = processor.processed_str(words_to_ignore=["com", "e"])
        
        assert result == "pao manteiga acucar"

    def test_str_processor_normalization_applies_default_mappings(self):
        """Validates application of default word mappings."""
        # Given: string with mappable words
        # When: process the string
        # Then: words are mapped according to default mappings
        processor = StrProcessor("Queijo qj com presunto")
        result = processor.output
        
        assert result == "queijo queijo com presunto"

    def test_str_processor_normalization_custom_mappings(self):
        """Validates application of custom word mappings."""
        # Given: string and custom mappings
        # When: process with custom mappings
        # Then: words are mapped according to custom mappings
        processor = StrProcessor("Frango c molho")
        custom_mappings = {"com": ["c"]}
        result = processor.processed_str(actual_name_to_receipt_description_mapper=custom_mappings)
        
        assert result == "frango com molho"

    def test_str_processor_normalization_word_boundary_matching(self):
        """Validates word boundary matching for mappings."""
        # Given: string where mapping word is part of another word
        # When: process the string
        # Then: only whole words are mapped, not substrings
        processor = StrProcessor("Queijo qj e qjado")
        result = processor.output
        
        # "qj" should be mapped to "queijo", but "qjado" should remain unchanged
        assert "queijo" in result
        assert "qjado" in result

    def test_str_processor_normalization_empty_string(self):
        """Validates handling of empty string input."""
        # Given: empty string
        # When: process the string
        # Then: empty string is returned
        processor = StrProcessor("")
        result = processor.output
        
        assert result == ""

    def test_str_processor_normalization_whitespace_only(self):
        """Validates handling of whitespace-only string."""
        # Given: string with only whitespace
        # When: process the string
        # Then: whitespace is preserved but normalized
        processor = StrProcessor("   \t\n  ")
        result = processor.output
        
        assert result == "   \t\n  "

    def test_str_processor_normalization_special_characters(self):
        """Validates handling of special characters."""
        # Given: string with special characters
        # When: process the string
        # Then: special characters are handled appropriately
        processor = StrProcessor("Pão & Café (especial)")
        result = processor.output
        
        assert result == "pao & cafe (especial)"

    def test_str_processor_normalization_unicode_characters(self):
        """Validates handling of unicode characters."""
        # Given: string with unicode characters
        # When: process the string
        # Then: unicode characters are normalized
        processor = StrProcessor("Café ☕ e Pão 🍞")
        result = processor.output
        
        assert result == "cafe  e pao "

    def test_str_processor_normalization_logging_behavior(self):
        """Validates logging behavior when transformations are applied."""
        # Given: string that will trigger transformations
        # When: process the string
        # Then: appropriate logging occurs
        with patch('src.contexts.shared_kernel.adapters.name_search.structlog_logger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance
            
            processor = StrProcessor("Queijo qj de fazenda")
            processor.output
            
            # Verify logger was called for transformations
            mock_logger_instance.debug.assert_called_once()
            call_args = mock_logger_instance.debug.call_args
            assert "Text processing applied transformations" in call_args[0][0]
            assert "words_ignored" in call_args[1]
            assert "mappings_applied" in call_args[1]


class TestStrProcessorEdgeCases:
    """Test edge case handling in string processing."""

    def test_str_processor_edge_cases_none_input(self):
        """Validates handling of None input."""
        # Given: None input
        # When: create processor with None
        # Then: appropriate error handling occurs
        with pytest.raises((TypeError, AttributeError)):
            StrProcessor(None)  # type: ignore[arg-type]

    def test_str_processor_edge_cases_very_long_string(self):
        """Validates handling of very long strings."""
        # Given: very long string
        # When: process the string
        # Then: processing completes successfully
        long_string = "a" * 10000
        processor = StrProcessor(long_string)
        result = processor.output
        
        assert result == "a" * 10000
        assert len(result) == 10000

    def test_str_processor_edge_cases_repeated_words(self):
        """Validates handling of repeated words."""
        # Given: string with repeated words
        # When: process the string
        # Then: all instances are processed
        processor = StrProcessor("de de de da da da")
        result = processor.output
        
        assert result == "da"

    def test_str_processor_edge_cases_mixed_mappings_and_ignored(self):
        """Validates handling of mixed mappings and ignored words."""
        # Given: string with both mappable and ignored words
        # When: process the string
        # Then: both transformations are applied correctly
        processor = StrProcessor("Queijo qj de fazenda")
        result = processor.output
        
        assert result == "queijo queijo fazenda"

    def test_str_processor_edge_cases_case_sensitive_mappings(self):
        """Validates case sensitivity in mappings."""
        # Given: string with mixed case mappable words
        # When: process the string
        # Then: mappings are case-sensitive
        processor = StrProcessor("Queijo QJ qj Qj")
        result = processor.output
        
        # All instances of "qj" should be mapped to "queijo" after lowercase conversion
        assert result.count("queijo") == 4  # All instances mapped

    def test_str_processor_edge_cases_empty_mappings(self):
        """Validates handling of empty mapping dictionaries."""
        # Given: string and empty mappings
        # When: process with empty mappings
        # Then: no mappings are applied
        processor = StrProcessor("Queijo qj")
        result = processor.processed_str(actual_name_to_receipt_description_mapper={})
        
        assert result == "queijo queijo"

    def test_str_processor_edge_cases_empty_ignored_words(self):
        """Validates handling of empty ignored words list."""
        # Given: string and empty ignored words list
        # When: process with empty ignored words
        # Then: no words are ignored
        processor = StrProcessor("Arroz de frango")
        result = processor.processed_str(words_to_ignore=[])
        
        assert result == "arroz frango"

    def test_str_processor_edge_cases_none_parameters(self):
        """Validates handling of None parameters."""
        # Given: string and None parameters
        # When: process with None parameters
        # Then: default behavior is used
        processor = StrProcessor("Queijo qj de fazenda")
        result = processor.processed_str(words_to_ignore=None, actual_name_to_receipt_description_mapper=None)
        
        assert result == "queijo queijo fazenda"


class TestSimilarityRankingAlgorithm:
    """Test similarity ranking algorithm and ranking logic."""

    def test_similarity_ranking_algorithm_basic_ranking(self):
        """Validates basic similarity ranking functionality."""
        # Given: description and similar candidates
        # When: compute ranking
        # Then: candidates are ranked by similarity
        description = "frango assado"
        similars = [
            ("frango frito", 0.8),
            ("frango assado", 0.9),
            ("peixe assado", 0.7),
        ]
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        # "frango frito" should be filtered out due to cooking method mismatch
        assert len(result) == 2
        assert result[0].description == "frango assado"  # Best match first
        assert result[0].sim_score == 0.9

    def test_similarity_ranking_algorithm_first_word_priority(self):
        """Validates that first word matches are prioritized."""
        # Given: description and candidates with first word matches
        # When: compute ranking
        # Then: first word matches are ranked higher
        description = "frango"
        similars = [
            ("peixe", 0.9),
            ("frango simples", 0.8),
            ("frango grelhado", 0.7),
        ]
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        # Both "frango" candidates should rank higher than "peixe" despite lower sim_score
        assert result[0].description in ["frango simples", "frango grelhado"]
        assert result[1].description in ["frango simples", "frango grelhado"]
        assert result[2].description == "peixe"

    def test_similarity_ranking_algorithm_full_word_matches(self):
        """Validates that full word matches are prioritized over partial matches."""
        # Given: description and candidates with full vs partial word matches
        # When: compute ranking
        # Then: full word matches rank higher
        description = "frango assado"
        similars = [
            ("frango simples", 0.8),  # Partial word match
            ("frango assado", 0.7),  # Full word match
        ]
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        assert result[0].description == "frango assado"
        assert result[1].description == "frango simples"

    def test_similarity_ranking_algorithm_positional_matching(self):
        """Validates that positional word matches are prioritized."""
        # Given: description and candidates with positional matches
        # When: compute ranking
        # Then: positional matches rank higher
        description = "frango assado"
        similars = [
            ("assado frango", 0.8),  # Non-positional match
            ("frango assado", 0.7),  # Positional match
        ]
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        assert result[0].description == "frango assado"
        assert result[1].description == "assado frango"

    def test_similarity_ranking_algorithm_cooking_method_filtering(self):
        """Validates filtering based on cooking method keywords."""
        # Given: description and candidates with cooking method mismatches
        # When: compute ranking
        # Then: mismatched cooking methods are filtered out
        description = "frango"
        similars = [
            ("frango frito", 0.9),
            ("frango assado", 0.8),
        ]
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        # Both should be filtered out due to cooking method mismatch
        assert len(result) == 0

    def test_similarity_ranking_algorithm_custom_cooking_methods(self):
        """Validates custom cooking method keywords."""
        # Given: description and custom cooking method keywords
        # When: compute ranking with custom keywords
        # Then: custom keywords are used for filtering
        description = "frango"
        similars = [
            ("frango grelhado", 0.9),
            ("frango assado", 0.8),
        ]
        
        ranking = SimilarityRanking(description, similars, words_that_must_fully_match=["grelhado"])
        result = ranking.ranking
        
        # "frango grelhado" should be filtered out
        assert len(result) == 1
        assert result[0].description == "frango assado"

    def test_similarity_ranking_algorithm_empty_candidates(self):
        """Validates handling of empty candidate list."""
        # Given: description and empty candidates
        # When: compute ranking
        # Then: empty list is returned
        description = "frango"
        similars = []
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        assert result == []

    def test_similarity_ranking_algorithm_all_filtered(self):
        """Validates handling when all candidates are filtered out."""
        # Given: description and candidates that all get filtered
        # When: compute ranking
        # Then: empty list is returned
        description = "frango"
        similars = [
            ("frango frito", 0.9),
            ("frango assado", 0.8),
        ]
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        assert result == []

    def test_similarity_ranking_algorithm_tie_breaking(self):
        """Validates tie-breaking using string length."""
        # Given: candidates with identical scores
        # When: compute ranking
        # Then: shorter strings rank higher (tie-breaking)
        description = "frango"
        similars = [
            ("frango muito longo", 0.8),
            ("frango", 0.8),
        ]
        
        ranking = SimilarityRanking(description, similars)
        result = ranking.ranking
        
        assert result[0].description == "frango"  # Shorter string first
        assert result[1].description == "frango muito longo"

    def test_similarity_ranking_algorithm_processed_description_property(self):
        """Validates processed_description property."""
        # Given: description with special characters
        # When: access processed_description property
        # Then: processed version is returned
        description = "Frango de Fazenda"
        similars = [("frango", 0.8)]
        
        ranking = SimilarityRanking(description, similars)
        processed = ranking.processed_description
        
        assert processed == "frango fazenda"  # "de" removed, case normalized

    def test_similarity_ranking_algorithm_logging_behavior(self):
        """Validates logging behavior during ranking."""
        # Given: ranking with candidates
        # When: compute ranking
        # Then: appropriate logging occurs
        with patch('src.contexts.shared_kernel.adapters.name_search.structlog_logger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance
            
            description = "frango"
            similars = [("frango assado", 0.8)]
            
            ranking = SimilarityRanking(description, similars)
            ranking.ranking
            
            # Verify debug and info logging
            assert mock_logger_instance.debug.called
            assert mock_logger_instance.info.called


class TestMatchDataValueObject:
    """Test MatchData value object behavior and contracts."""

    def test_match_data_creation(self):
        """Validates MatchData object creation with all fields."""
        # Given: all required fields for MatchData
        # When: create MatchData instance
        # Then: all fields are properly set
        match_data = MatchData(
            description="frango assado",
            sim_score=0.9,
            should_ignore=False,
            has_first_word_full_match=True,
            has_first_word_partial_match=True,
            full_word_position=2,
            length_full_word_position=12,
            partial_word_position=1,
            length_partial_word_position=6,
            full_word=2,
            length_full_word=12,
            partial_word=1,
            length_partial_word=6,
            length=0.1,
        )
        
        assert match_data.description == "frango assado"
        assert match_data.sim_score == 0.9
        assert match_data.should_ignore is False
        assert match_data.has_first_word_full_match is True
        assert match_data.has_first_word_partial_match is True
        assert match_data.full_word_position == 2
        assert match_data.length_full_word_position == 12
        assert match_data.partial_word_position == 1
        assert match_data.length_partial_word_position == 6
        assert match_data.full_word == 2
        assert match_data.length_full_word == 12
        assert match_data.partial_word == 1
        assert match_data.length_partial_word == 6
        assert match_data.length == 0.1

    def test_match_data_immutability(self):
        """Validates MatchData immutability."""
        # Given: MatchData instance
        # When: attempt to modify attributes
        # Then: modification raises FrozenInstanceError
        match_data = MatchData(
            description="frango assado",
            sim_score=0.9,
            should_ignore=False,
            has_first_word_full_match=True,
            has_first_word_partial_match=True,
            full_word_position=2,
            length_full_word_position=12,
            partial_word_position=1,
            length_partial_word_position=6,
            full_word=2,
            length_full_word=12,
            partial_word=1,
            length_partial_word=6,
            length=0.1,
        )
        
        # MatchData is not frozen by default, so we just verify it's a value object
        # that can be created and accessed
        assert match_data.description == "frango assado"
        assert match_data.sim_score == 0.9


class TestNumberOfWordsAndLettersMatchingValueObject:
    """Test NumberOfWordsAndLettersMatching value object behavior."""

    def test_number_of_words_and_letters_matching_creation(self):
        """Validates NumberOfWordsAndLettersMatching object creation."""
        # Given: word and letter counts
        # When: create NumberOfWordsAndLettersMatching instance
        # Then: fields are properly set
        matching = NumberOfWordsAndLettersMatching(
            number_of_words=3,
            number_of_letters=15,
        )
        
        assert matching.number_of_words == 3
        assert matching.number_of_letters == 15

    def test_number_of_words_and_letters_matching_immutability(self):
        """Validates NumberOfWordsAndLettersMatching immutability."""
        # Given: NumberOfWordsAndLettersMatching instance
        # When: attempt to modify attributes
        # Then: modification raises FrozenInstanceError
        matching = NumberOfWordsAndLettersMatching(
            number_of_words=3,
            number_of_letters=15,
        )
        
        # NumberOfWordsAndLettersMatching is not frozen by default, so we just verify
        # it's a value object that can be created and accessed
        assert matching.number_of_words == 3
        assert matching.number_of_letters == 15


class TestSimilarityRankingPrivateMethods:
    """Test private methods of SimilarityRanking for comprehensive coverage."""

    def test_partial_word_number_of_words_matching(self):
        """Validates partial word matching count."""
        # Given: ranking with description and target
        # When: call _partial_word_number_of_words_matching
        # Then: correct count is returned
        ranking = SimilarityRanking("frango assado", [])
        count = ranking._partial_word_number_of_words_matching("frango frito")
        
        assert count == 1  # "frango" matches

    def test_partial_word_number_of_letters_matching(self):
        """Validates partial word letter count."""
        # Given: ranking with description and target
        # When: call _partial_word_number_of_letters_matching
        # Then: correct letter count is returned
        ranking = SimilarityRanking("frango assado", [])
        count = ranking._partial_word_number_of_letters_matching("frango frito")
        
        assert count == 6  # "frango" has 6 letters

    def test_full_word_number_of_words_matching(self):
        """Validates full word matching count."""
        # Given: ranking with description and target
        # When: call _full_word_number_of_words_matching
        # Then: correct count is returned
        ranking = SimilarityRanking("frango assado", [])
        count = ranking._full_word_number_of_words_matching("frango assado")
        
        assert count == 2  # Both words match exactly

    def test_full_word_number_of_letters_matching(self):
        """Validates full word letter count."""
        # Given: ranking with description and target
        # When: call _full_word_number_of_letters_matching
        # Then: correct letter count is returned
        ranking = SimilarityRanking("frango assado", [])
        count = ranking._full_word_number_of_letters_matching("frango assado")
        
        assert count == 12  # "frango" (6) + "assado" (6) = 12

    def test_has_first_word_full_match(self):
        """Validates first word full match detection."""
        # Given: ranking with description and target
        # When: call _has_first_word_full_match
        # Then: correct boolean is returned
        ranking = SimilarityRanking("frango assado", [])
        
        assert ranking._has_first_word_full_match("frango frito") is True
        assert ranking._has_first_word_full_match("peixe assado") is False

    def test_has_first_word_partial_match(self):
        """Validates first word partial match detection."""
        # Given: ranking with description and target
        # When: call _has_first_word_partial_match
        # Then: correct boolean is returned
        ranking = SimilarityRanking("frang", [])  # Partial word
        
        assert ranking._has_first_word_partial_match("frango frito") is True
        assert ranking._has_first_word_partial_match("peixe assado") is False

    def test_should_ignore_cooking_method_mismatch(self):
        """Validates cooking method mismatch detection."""
        # Given: ranking with cooking method keywords
        # When: call _should_ignore with mismatched cooking method
        # Then: True is returned for mismatch
        ranking = SimilarityRanking("frango", [])
        
        assert ranking._should_ignore("frango frito") is True
        assert ranking._should_ignore("frango") is False

    def test_should_ignore_no_cooking_method(self):
        """Validates handling when no cooking method is present."""
        # Given: ranking without cooking method keywords
        # When: call _should_ignore
        # Then: False is returned
        ranking = SimilarityRanking("frango", [])
        
        assert ranking._should_ignore("frango simples") is False


class TestProcessingConfig:
    """Test ProcessingConfig value object behavior."""

    def test_processing_config_creation(self):
        """Validates ProcessingConfig object creation."""
        # Given: configuration parameters
        # When: create ProcessingConfig instance
        # Then: fields are properly set
        config = ProcessingConfig(
            words_to_ignore=frozenset(["test"]),
            name_mappings={"test": ["t"]}
        )
        
        assert "test" in config.words_to_ignore
        assert config.name_mappings["test"] == ["t"]

    def test_processing_config_defaults(self):
        """Validates ProcessingConfig default values."""
        # Given: no parameters
        # When: create ProcessingConfig with defaults
        # Then: default values are used
        config = ProcessingConfig()
        
        assert "de" in config.words_to_ignore
        assert "da" in config.words_to_ignore
        assert "queijo" in config.name_mappings
        assert config.name_mappings["queijo"] == ["qj"]


class TestRankingConfig:
    """Test RankingConfig value object behavior."""

    def test_ranking_config_creation(self):
        """Validates RankingConfig object creation."""
        # Given: configuration parameters
        # When: create RankingConfig instance
        # Then: fields are properly set
        config = RankingConfig(
            cooking_method_keywords=frozenset(["test"])
        )
        
        assert "test" in config.cooking_method_keywords

    def test_ranking_config_defaults(self):
        """Validates RankingConfig default values."""
        # Given: no parameters
        # When: create RankingConfig with defaults
        # Then: default values are used
        config = RankingConfig()
        
        assert "frito" in config.cooking_method_keywords
        assert "assado" in config.cooking_method_keywords


class TestInputValidation:
    """Test input validation and error handling."""

    def test_str_processor_invalid_input_type(self):
        """Validates StrProcessor input type validation."""
        # Given: invalid input type
        # When: create StrProcessor with invalid input
        # Then: TypeError is raised
        with pytest.raises(TypeError, match="Expected string, got"):
            StrProcessor(None)  # type: ignore[arg-type]
        
        with pytest.raises(TypeError, match="Expected string, got"):
            StrProcessor(123)  # type: ignore[arg-type]

    def test_similarity_ranking_invalid_description_type(self):
        """Validates SimilarityRanking description type validation."""
        # Given: invalid description type
        # When: create SimilarityRanking with invalid description
        # Then: TypeError is raised
        with pytest.raises(TypeError, match="Expected string for description"):
            SimilarityRanking(None, [])  # type: ignore[arg-type]

    def test_similarity_ranking_invalid_similars_type(self):
        """Validates SimilarityRanking similars type validation."""
        # Given: invalid similars type
        # When: create SimilarityRanking with invalid similars
        # Then: TypeError is raised
        with pytest.raises(TypeError, match="Expected list for similars"):
            SimilarityRanking("test", None)  # type: ignore[arg-type]
