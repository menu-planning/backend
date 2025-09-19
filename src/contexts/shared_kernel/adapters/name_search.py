"""String preprocessing and similarity ranking utilities for name search.

Exposes `StrProcessor` for basic normalization and `SimilarityRanking` to rank
candidate names, with heuristics to enforce full-word matches for certain
keywords.
"""
import operator
import re
from collections.abc import Mapping
from typing import Final

from attrs import define
from src.logging.logger import get_logger
from unidecode import unidecode


@define(frozen=True)
class ProcessingConfig:
    """Configuration for string processing operations.
    
    Attributes:
        words_to_ignore: Common words to remove during processing.
        name_mappings: Mapping from standard names to abbreviated forms.
    """
    words_to_ignore: frozenset[str] = frozenset([
        "de",
        "da",
    ])
    name_mappings: Mapping[str, list[str]] = {
        "queijo": ["qj"],
        "ct": ["contra"],
        "mozarela": ["mus"],
        "costela": ["costelinha"],
        "porco": ["suina"],
        "com": ["c"],
        "sem": ["s"],
    }


class StrProcessor:
    """String processor for normalizing text input for similarity comparisons.

    Applies text normalization including accent removal, case conversion,
    and custom word substitutions to enable consistent string matching.
    """

    # Default configuration
    DEFAULT_CONFIG: Final[ProcessingConfig] = ProcessingConfig()

    def __init__(self, input: str):
        """Initialize processor with input string.

        Args:
            input: Raw string to be processed.
            
        Raises:
            TypeError: If input is not a string.
        """
        if not isinstance(input, str):
            raise TypeError(f"Expected string, got {type(input).__name__}")
        
        self.description = input
        self.logger = get_logger("name_search.str_processor")
        self._processed_cache: dict[str, str] = {}

    def processed_str(
        self,
        words_to_ignore: list[str] | None = None,
        actual_name_to_receipt_description_mapper: Mapping[str, list[str]] | None = None,
    ) -> str:
        """Return normalized string applying configured substitutions.

        Args:
            words_to_ignore: Override default words to ignore.
            actual_name_to_receipt_description_mapper: Override default name mappings.

        Returns:
            Normalized string with accents removed, lowercase, and substitutions applied.
        """
        # Create cache key for this configuration
        cache_key = f"{words_to_ignore}_{actual_name_to_receipt_description_mapper}"
        if cache_key in self._processed_cache:
            return self._processed_cache[cache_key]

        original = self.description
        normalized_text = self._normalize_text(original)
        
        # Get configuration
        config = self._get_config(words_to_ignore, actual_name_to_receipt_description_mapper)
        
        # Apply transformations
        words_ignored, mappings_applied, result = self._apply_transformations(normalized_text, config)
        
        # Log transformations if any were applied
        if words_ignored or mappings_applied:
            self.logger.debug(
                "Text processing applied transformations",
                original_text=original,
                processed_text=result,
                words_ignored=words_ignored,
                mappings_applied=mappings_applied
            )

        # Cache the result
        self._processed_cache[cache_key] = result
        return result

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing accents, commas, and converting to lowercase.
        
        Args:
            text: Input text to normalize.
            
        Returns:
            Normalized text.
        """
        return unidecode(text).replace(",", "").lower()

    def _get_config(
        self,
        words_to_ignore: list[str] | None,
        name_mappings: Mapping[str, list[str]] | None,
    ) -> ProcessingConfig:
        """Get processing configuration from parameters or defaults.
        
        Args:
            words_to_ignore: Custom words to ignore.
            name_mappings: Custom name mappings.
            
        Returns:
            Processing configuration to use.
        """
        if words_to_ignore is None and name_mappings is None:
            return self.DEFAULT_CONFIG
        
        return ProcessingConfig(
            words_to_ignore=frozenset(words_to_ignore) if words_to_ignore else self.DEFAULT_CONFIG.words_to_ignore,
            name_mappings=name_mappings if name_mappings else self.DEFAULT_CONFIG.name_mappings,
        )

    def _apply_transformations(
        self, text: str, config: ProcessingConfig
    ) -> tuple[list[str], list[str], str]:
        """Apply word removal and mapping transformations.
        
        Args:
            text: Text to transform.
            config: Processing configuration.
            
        Returns:
            Tuple of (ignored_words, applied_mappings, transformed_text).
        """
        words_ignored = []
        mappings_applied = []
        result = text
        
        # Remove ignored words
        for word in config.words_to_ignore:
            word_with_space = f"{word} "
            if word_with_space in result:
                words_ignored.append(word)
                result = result.replace(word_with_space, "")
        
        # Apply word mappings
        for standard_name, abbreviations in config.name_mappings.items():
            for abbreviation in abbreviations:
                pattern = rf"\b{re.escape(abbreviation)}\b"
                if re.search(pattern, result):
                    mappings_applied.append(f"{abbreviation}->{standard_name}")
                    result = re.sub(pattern, standard_name, result)
        
        return words_ignored, mappings_applied, result

    @property
    def output(self) -> str:
        """Return default-processed string output.

        Returns:
            String processed with default configuration.
        """
        return self.processed_str()


@define
class NumberOfWordsAndLettersMatching:
    """Value object representing word and letter match counts.

    Attributes:
        number_of_words: Count of matching words.
        number_of_letters: Count of matching letters.
    """
    number_of_words: int
    number_of_letters: int


@define
class MatchData:
    """Value object containing detailed match information for ranking.

    Attributes:
        description: Original description string.
        sim_score: Similarity score from external algorithm.
        should_ignore: Whether this match should be filtered out.
        has_first_word_full_match: First word matches exactly.
        has_first_word_partial_match: First word is contained in target.
        full_word_position: Count of full word matches at same positions.
        length_full_word_position: Total length of positionally matched full words.
        partial_word_position: Count of partial word matches at same positions.
        length_partial_word_position: Total length of positionally matched partial words.
        full_word: Count of full word matches anywhere.
        length_full_word: Total length of full word matches.
        partial_word: Count of partial word matches anywhere.
        length_partial_word: Total length of partial word matches.
        length: Reciprocal of target string length for tie-breaking.
    """
    description: str
    sim_score: float
    should_ignore: bool
    has_first_word_full_match: bool
    has_first_word_partial_match: bool
    full_word_position: int
    length_full_word_position: int
    partial_word_position: int
    length_partial_word_position: int
    full_word: int
    length_full_word: int
    partial_word: int
    length_partial_word: int
    length: float


@define(frozen=True)
class RankingConfig:
    """Configuration for similarity ranking operations.
    
    Attributes:
        cooking_method_keywords: Keywords that require exact matches.
    """
    cooking_method_keywords: frozenset[str] = frozenset([
        "frito",
        "frita", 
        "assado",
        "assada",
        "cozido",
        "cozida",
    ])


class SimilarityRanking:
    """Rank similar names using multiple partial/full word heuristics.

    Computes comprehensive similarity metrics combining external similarity scores
    with custom word-matching algorithms to provide better ranking for recipe names.
    """

    # Default configuration
    DEFAULT_CONFIG: Final[RankingConfig] = RankingConfig()

    def __init__(
        self,
        description: str,
        similars: list[tuple[str, float]],
        words_that_must_fully_match: list[str] | None = None,
    ):
        """Initialize ranking with description and candidate names.

        Args:
            description: Query string to find matches for.
            similars: Pre-computed similarity scores from external algorithm.
            words_that_must_fully_match: Cooking method keywords requiring exact matches.
            
        Raises:
            TypeError: If description is not a string or similars is not a list.
        """
        if not isinstance(description, str):
            raise TypeError(f"Expected string for description, got {type(description).__name__}")
        if not isinstance(similars, list):
            raise TypeError(f"Expected list for similars, got {type(similars).__name__}")
        
        self.description = description
        self.similars = similars
        self.str_processor = StrProcessor
        self.config = RankingConfig(
            cooking_method_keywords=frozenset(words_that_must_fully_match) 
            if words_that_must_fully_match 
            else self.DEFAULT_CONFIG.cooking_method_keywords
        )
        self.logger = get_logger("name_search.similarity_ranking")
        
        # Cache for processed strings to avoid repeated processing
        self._processed_cache: dict[str, str] = {}
        self._processed_description: str | None = None

    @property
    def processed_description(self) -> str:
        """Processed form of the query description used in comparisons.

        Returns:
            Normalized description string for consistent matching.
        """
        if self._processed_description is None:
            self._processed_description = self.str_processor(self.description).output
        return self._processed_description

    def _get_processed_string(self, text: str) -> str:
        """Get processed string with caching.
        
        Args:
            text: Text to process.
            
        Returns:
            Processed text.
        """
        if text not in self._processed_cache:
            self._processed_cache[text] = self.str_processor(text).output
        return self._processed_cache[text]

    def _partial_word_number_of_words_matching(self, processed_db_name: str) -> int:
        """Count words from query that are contained in target name.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Count of query words found as substrings in target.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        return sum(a in b for a in query_words for b in target_words)

    def _partial_word_number_of_letters_matching(self, processed_db_name: str) -> int:
        """Count total letters from matching partial words.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Sum of lengths of query words found as substrings in target.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        return sum(len(a) for a in query_words for b in target_words if a in b)

    def _partial_word_positional_matching(self, processed_db_name: str) -> tuple[int, int]:
        """Count partial word matches at same positions.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Tuple of (count, total_length) for positionally matched partial words.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        length = min(len(query_words), len(target_words))
        count = 0
        length_matching = 0
        for i in range(length):
            if query_words[i] in target_words[i]:
                count += 1
                length_matching += len(query_words[i])
        return (count, length_matching)

    def _partial_word_number_of_words_with_positional_matching(
        self, processed_db_name: str
    ) -> int:
        """Count partial word matches at same positions.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Count of positionally matched partial words.
        """
        return self._partial_word_positional_matching(processed_db_name)[0]

    def _partial_word_number_of_letters_with_positional_matching(
        self, processed_db_name: str
    ) -> int:
        """Count total letters from positionally matched partial words.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Total length of positionally matched partial words.
        """
        return self._partial_word_positional_matching(processed_db_name)[1]

    def _has_first_word_full_match(self, processed_db_name: str) -> bool:
        """Check if first word matches exactly.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            True if first words match exactly, False otherwise.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        if not query_words or not target_words:
            return False
        return query_words[0] == target_words[0]

    def _has_first_word_partial_match(self, processed_db_name: str) -> bool:
        """Check if first word is contained in target's first word.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            True if first query word is substring of first target word.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        if not query_words or not target_words:
            return False
        return query_words[0] in target_words[0]

    def _full_word_number_of_words_matching(self, processed_db_name: str) -> int:
        """Count exact word matches between query and target.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Count of words that match exactly after normalization.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        return sum(
            self._get_processed_string(a) == self._get_processed_string(b)
            for a in query_words
            for b in target_words
        )

    def _full_word_number_of_letters_matching(self, processed_db_name: str) -> int:
        """Count total letters from exact word matches.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Sum of lengths of exactly matched words.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        return sum(
            len(self._get_processed_string(a))
            for a in query_words
            for b in target_words
            if self._get_processed_string(a) == self._get_processed_string(b)
        )

    def _full_word_positional_matching(self, processed_db_name: str) -> tuple[int, int]:
        """Count exact word matches at same positions.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Tuple of (count, total_length) for positionally matched exact words.
        """
        query_words = self.processed_description.split()
        target_words = processed_db_name.split()
        length = min(len(query_words), len(target_words))
        count = 0
        length_matching = 0
        for i in range(length):
            if query_words[i] == target_words[i]:
                count += 1
                length_matching += len(query_words[i])
        return (count, length_matching)

    def _full_word_number_of_words_with_positional_matching(
        self, processed_db_name: str
    ) -> int:
        """Count exact word matches at same positions.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Count of positionally matched exact words.
        """
        return self._full_word_positional_matching(processed_db_name)[0]

    def _full_word_number_of_letters_with_positional_matching(
        self, processed_db_name: str
    ) -> int:
        """Count total letters from positionally matched exact words.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Total length of positionally matched exact words.
        """
        return self._full_word_positional_matching(processed_db_name)[1]

    def _should_ignore(self, processed_db_name: str) -> bool:
        """Determine if match should be filtered based on cooking method keywords.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            True if target contains cooking method keywords not in query.
        """
        for word in self.config.cooking_method_keywords:
            # Use pre-compiled patterns for better performance
            pattern = rf"\b{re.escape(word)}\b"
            db_has_word = re.search(pattern, processed_db_name)
            description_has_word = re.search(pattern, self.processed_description)

            if db_has_word and not description_has_word:
                self.logger.debug(
                    "Product ignored due to cooking method mismatch",
                    product_name=processed_db_name,
                    search_description=self.processed_description,
                    mismatched_word=word,
                    reason="cooking_method_mismatch"
                )
                return True
        return False

    @property
    def ranking(self):
        """Compute comprehensive ranking of similar names.

        Combines external similarity scores with custom word-matching metrics
        to provide better ranking for recipe name searches.

        Returns:
            List of MatchData objects sorted by relevance score.
        """
        self.logger.debug(
            "Starting product ranking",
            search_description=self.description,
            processed_description=self.processed_description,
            candidate_count=len(self.similars),
            must_match_words=self.config.cooking_method_keywords
        )

        match_list = self._create_match_data_list()
        sorted_ranking = self._sort_matches(match_list)
        final_ranking = self._filter_ignored_matches(sorted_ranking)
        
        self._log_ranking_results(len(match_list), len(final_ranking))
        
        return final_ranking

    def _create_match_data_list(self) -> list[MatchData]:
        """Create list of MatchData objects for all candidates.
        
        Returns:
            List of MatchData objects with computed metrics.
        """
        match_list: list[MatchData] = []
        for name, sim in self.similars:
            preprocessed_name = self._get_processed_string(name)
            match_data = self._compute_match_metrics(name, sim, preprocessed_name)
            match_list.append(match_data)
        return match_list

    def _compute_match_metrics(self, name: str, sim: float, preprocessed_name: str) -> MatchData:
        """Compute all matching metrics for a single candidate.
        
        Args:
            name: Original candidate name.
            sim: Similarity score from external algorithm.
            preprocessed_name: Processed candidate name.
            
        Returns:
            MatchData object with all computed metrics.
        """
        return MatchData(
            description=name,
            sim_score=sim,
            should_ignore=self._should_ignore(preprocessed_name),
            has_first_word_full_match=self._has_first_word_full_match(preprocessed_name),
            has_first_word_partial_match=self._has_first_word_partial_match(preprocessed_name),
            full_word_position=self._full_word_number_of_words_with_positional_matching(preprocessed_name),
            length_full_word_position=self._full_word_number_of_letters_with_positional_matching(preprocessed_name),
            partial_word_position=self._partial_word_number_of_words_with_positional_matching(preprocessed_name),
            length_partial_word_position=self._partial_word_number_of_letters_with_positional_matching(preprocessed_name),
            full_word=self._full_word_number_of_words_matching(preprocessed_name),
            length_full_word=self._full_word_number_of_letters_matching(preprocessed_name),
            partial_word=self._partial_word_number_of_words_matching(preprocessed_name),
            length_partial_word=self._partial_word_number_of_letters_matching(preprocessed_name),
            length=1 / len(preprocessed_name) if preprocessed_name else 0,
        )

    def _sort_matches(self, match_list: list[MatchData]) -> list[MatchData]:
        """Sort matches by relevance score.
        
        Args:
            match_list: List of MatchData objects to sort.
            
        Returns:
            Sorted list of MatchData objects.
        """
        return sorted(
            match_list,
            key=operator.attrgetter(
                "has_first_word_full_match",
                "has_first_word_partial_match",
                "full_word_position",
                "length_full_word_position",
                "partial_word_position",
                "length_partial_word_position",
                "full_word",
                "length_full_word",
                "partial_word",
                "length_partial_word",
                "sim_score",
                "length",
            ),
            reverse=True,
        )

    def _filter_ignored_matches(self, ranking: list[MatchData]) -> list[MatchData]:
        """Filter out matches that should be ignored.
        
        Args:
            ranking: Sorted list of MatchData objects.
            
        Returns:
            Filtered list excluding ignored matches.
        """
        return [match for match in ranking if not match.should_ignore]

    def _log_ranking_results(self, total_candidates: int, final_results: int) -> None:
        """Log ranking completion results.
        
        Args:
            total_candidates: Total number of candidates processed.
            final_results: Number of results after filtering.
        """
        ignored_count = total_candidates - final_results
        self.logger.info(
            "Product ranking completed",
            search_description=self.description,
            total_candidates=total_candidates,
            ignored_products=ignored_count,
            final_results=final_results,
        )
