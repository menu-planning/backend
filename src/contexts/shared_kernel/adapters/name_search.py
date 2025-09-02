"""String preprocessing and similarity ranking utilities for name search.

Exposes `StrProcessor` for basic normalization and `SimilarityRanking` to rank
candidate names, with heuristics to enforce full-word matches for certain
keywords.
"""
import operator
import re
from collections.abc import Mapping

from attrs import define
from src.logging.logger import structlog_logger
from unidecode import unidecode


class StrProcessor:
    """String processor for normalizing text input for similarity comparisons.

    Applies text normalization including accent removal, case conversion,
    and custom word substitutions to enable consistent string matching.

    Attributes:
        words_to_ignore: Common words to remove during processing.
        actual_name_to_receipt_description_mapper: Mapping from standard names
            to abbreviated forms found in receipts.
    """
    words_to_ignore: frozenset[str] = frozenset([
        "de",
        "da",
    ])
    actual_name_to_receipt_description_mapper: Mapping[str, list[str]] = {
        "queijo": ["qj"],
        "ct": ["contra"],
        "mozarela": ["mus"],
        "costela": ["costelinha"],
        "porco": ["suina"],
        "com": ["c"],
        "sem": ["s"],
    }

    def __init__(self, input: str):
        """Initialize processor with input string.

        Args:
            input: Raw string to be processed.
        """
        self.description = input
        self.logger = structlog_logger("name_search.str_processor")

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
        original = self.description
        tmp = unidecode(self.description)
        tmp = tmp.replace(",", "")
        tmp = tmp.lower()

        # Remove ignored words
        words_ignored = []
        for word in (
            f"{word} " for word in words_to_ignore or StrProcessor.words_to_ignore
        ):
            if word in tmp:
                words_ignored.append(word.strip())
                tmp = tmp.replace(word, "")

        # Apply word mappings
        mappings_applied = []
        for k, v in (
            actual_name_to_receipt_description_mapper.items()
            if actual_name_to_receipt_description_mapper
            else StrProcessor.actual_name_to_receipt_description_mapper.items()
        ):
            for word in v:
                if re.search(rf"\b{word}\b", tmp):
                    mappings_applied.append(f"{word}->{k}")
                    tmp = re.sub(rf"\b{word}\b", k, tmp)

        if words_ignored or mappings_applied:
            self.logger.debug(
                "Text processing applied transformations",
                original_text=original,
                processed_text=tmp,
                words_ignored=words_ignored,
                mappings_applied=mappings_applied
            )

        return tmp

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


class SimilarityRanking:
    """Rank similar names using multiple partial/full word heuristics.

    Computes comprehensive similarity metrics combining external similarity scores
    with custom word-matching algorithms to provide better ranking for recipe names.

    Attributes:
        description: Query description to match against.
        similars: List of (name, similarity_score) tuples from external algorithm.
        words_that_must_fully_match: Keywords that require exact matches.
    """
    def __init__(
        self,
        description: str,
        similars: list[tuple[str,float]],
        words_that_must_fully_match: list[str] | None = None,
    ):
        """Initialize ranking with description and candidate names.

        Args:
            description: Query string to find matches for.
            similars: Pre-computed similarity scores from external algorithm.
            words_that_must_fully_match: Cooking method keywords requiring exact matches.
        """
        self.description = description
        self.similars = similars
        self.str_processor = StrProcessor
        self.words_that_must_fully_match = words_that_must_fully_match or [
            "frito",
            "frita",
            "assado",
            "assada",
            "cozido",
            "cozida",
        ]
        self.logger = structlog_logger("name_search.similarity_ranking")

    @property
    def processed_description(self) -> str:
        """Processed form of the query description used in comparisons.

        Returns:
            Normalized description string for consistent matching.
        """
        return self.str_processor(self.description).output

    def _partial_word_number_of_words_matching(self, processed_db_name: str) -> int:
        """Count words from query that are contained in target name.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Count of query words found as substrings in target.
        """
        return sum(
            [
                a in b
                for a in self.processed_description.split()
                for b in processed_db_name.split()
            ]
        )

    def _partial_word_number_of_letters_matching(self, processed_db_name: str) -> int:
        """Count total letters from matching partial words.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Sum of lengths of query words found as substrings in target.
        """
        return sum(
            [
                len(a)
                for a in self.processed_description.split()
                for b in processed_db_name.split()
                if a in b
            ]
        )

    def _partial_word_positional_matching(self, processed_db_name: str) -> tuple[int, int]:
        """Count partial word matches at same positions.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Tuple of (count, total_length) for positionally matched partial words.
        """
        length = min(
            len(self.processed_description.split()), len(processed_db_name.split())
        )
        count = 0
        length_matching = 0
        for i in range(length):
            if self.processed_description.split()[i] in processed_db_name.split()[i]:
                count += 1
                length_matching += len(self.processed_description.split()[i])
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
        first_word_in_description = self.processed_description.split()[0]
        first_word_in_db_name = processed_db_name.split()[0]
        return first_word_in_description == first_word_in_db_name

    def _has_first_word_partial_match(self, processed_db_name: str) -> bool:
        """Check if first word is contained in target's first word.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            True if first query word is substring of first target word.
        """
        first_word_in_description = self.processed_description.split()[0]
        first_word_in_db_name = processed_db_name.split()[0]
        return first_word_in_description in first_word_in_db_name

    def _full_word_number_of_words_matching(self, processed_db_name: str) -> int:
        """Count exact word matches between query and target.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Count of words that match exactly after normalization.
        """
        return sum(
            [
                self.str_processor(a).output == self.str_processor(b).output
                for a in self.processed_description.split()
                for b in processed_db_name.split()
            ]
        )

    def _full_word_number_of_letters_matching(self, processed_db_name: str) -> int:
        """Count total letters from exact word matches.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Sum of lengths of exactly matched words.
        """
        return sum(
            [
                len(self.str_processor(a).output)
                for a in self.processed_description.split()
                for b in processed_db_name.split()
                if self.str_processor(a).output == self.str_processor(b).output
            ]
        )

    def _full_word_positional_matching(self, processed_db_name: str) -> tuple[int, int]:
        """Count exact word matches at same positions.

        Args:
            processed_db_name: Normalized target name to check.

        Returns:
            Tuple of (count, total_length) for positionally matched exact words.
        """
        length = min(
            len(self.processed_description.split()), len(processed_db_name.split())
        )
        count = 0
        length_matching = 0
        for i in range(length):
            if self.processed_description.split()[i] == processed_db_name.split()[i]:
                count += 1
                length_matching += len(self.processed_description.split()[i])
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
        for word in self.words_that_must_fully_match:
            db_has_word = re.compile(rf"\b{word}\b").search(processed_db_name)
            description_has_word = re.compile(rf"\b{word}\b").search(self.processed_description)

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
            must_match_words=self.words_that_must_fully_match
        )

        match_list: list[MatchData] = []
        for name, sim in self.similars:
            preprocessed_name = self.str_processor(name).output
            match_list.append(
                MatchData(
                    description=name,
                    sim_score=sim,
                    should_ignore=self._should_ignore(preprocessed_name),
                    has_first_word_full_match=self._has_first_word_full_match(
                        preprocessed_name
                    ),
                    has_first_word_partial_match=self._has_first_word_partial_match(
                        preprocessed_name
                    ),
                    full_word_position=self._full_word_number_of_words_with_positional_matching(
                        preprocessed_name
                    ),
                    length_full_word_position=self._full_word_number_of_letters_with_positional_matching(
                        preprocessed_name
                    ),
                    partial_word_position=self._partial_word_number_of_words_with_positional_matching(
                        preprocessed_name
                    ),
                    length_partial_word_position=self._partial_word_number_of_letters_with_positional_matching(
                        preprocessed_name
                    ),
                    full_word=self._full_word_number_of_words_matching(
                        preprocessed_name
                    ),
                    length_full_word=self._full_word_number_of_letters_matching(
                        preprocessed_name
                    ),
                    partial_word=self._partial_word_number_of_words_matching(
                        preprocessed_name
                    ),
                    length_partial_word=self._partial_word_number_of_letters_matching(
                        preprocessed_name
                    ),
                    length=1 / len(preprocessed_name),
                )
            )
        ranking = sorted(
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

        final_ranking = [i for i in ranking if i.should_ignore is False]
        ignored_count = len(ranking) - len(final_ranking)

        self.logger.info(
            "Product ranking completed",
            search_description=self.description,
            total_candidates=len(self.similars),
            ignored_products=ignored_count,
            final_results=len(final_ranking),
            top_match=final_ranking[0].description if final_ranking else None,
            top_match_score=final_ranking[0].sim_score if final_ranking else None
        )

        return final_ranking
