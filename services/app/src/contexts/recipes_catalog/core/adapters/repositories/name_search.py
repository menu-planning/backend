import operator
import re

from attrs import define
from unidecode import unidecode


class StrProcessor:
    words_to_ignore: list[str] = [
        "de",
        "da",
    ]
    actual_name_to_receipt_description_mapper: dict[str, list[str]] = {
        "queijo": ["qj"],
        "ct": ["contra"],
        "mozarela": ["mus"],
        "costela": ["costelinha"],
        "porco": ["suina"],
        "com": ["c"],
        "sem": ["s"],
    }

    def __init__(self, input: str):
        self.description = input

    def processed_str(
        self,
        words_to_ignore: list[str] | None = None,
        actual_name_to_receipt_description_mapper: dict[str, list[str]] | None = None,
    ) -> str:
        tmp = unidecode(self.description)
        tmp = tmp.replace(",", "")
        tmp = tmp.lower()
        for word in (
            f"{word} " for word in words_to_ignore or StrProcessor.words_to_ignore
        ):
            tmp = tmp.replace(word, "")
        for k, v in (
            actual_name_to_receipt_description_mapper.items()
            if actual_name_to_receipt_description_mapper
            else StrProcessor.actual_name_to_receipt_description_mapper.items()
        ):
            for word in v:
                tmp = re.sub(rf"\b{word}\b", k, tmp)
        return tmp

    @property
    def output(self) -> str:
        return self.processed_str()


@define
class NumberOfWordsAndLettersMatching:
    number_of_words: int
    number_of_letters: int


@define
class MatchData:
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
    def __init__(
        self,
        description: str,
        similars: list[tuple[str,float]],
        words_that_must_fully_match: list[str] | None = None,
    ):
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

    @property
    def processed_description(self) -> str:
        return self.str_processor(self.description).output

    def _partial_word_number_of_words_matching(self, processed_db_name: str) -> int:
        return sum(
            [
                a in b
                for a in self.processed_description.split()
                for b in processed_db_name.split()
            ]
        )

    def _partial_word_number_of_letters_matching(self, processed_db_name: str) -> int:
        return sum(
            [
                len(a)
                for a in self.processed_description.split()
                for b in processed_db_name.split()
                if a in b
            ]
        )

    def _partial_word_positional_matching(self, processed_db_name: str) -> tuple[int, int]:
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
        return self._partial_word_positional_matching(processed_db_name)[0]

    def _partial_word_number_of_letters_with_positional_matching(
        self, processed_db_name: str
    ) -> int:
        return self._partial_word_positional_matching(processed_db_name)[1]

    def _has_first_word_full_match(self, processed_db_name: str) -> bool:
        first_word_in_description = self.processed_description.split()[0]
        first_word_in_db_name = processed_db_name.split()[0]
        if first_word_in_description == first_word_in_db_name:
            return True
        return False

    def _has_first_word_partial_match(self, processed_db_name: str) -> bool:
        first_word_in_description = self.processed_description.split()[0]
        first_word_in_db_name = processed_db_name.split()[0]
        if first_word_in_description in first_word_in_db_name:
            return True
        return False

    def _full_word_number_of_words_matching(self, processed_db_name: str) -> int:
        return sum(
            [
                self.str_processor(a).output == self.str_processor(b).output
                for a in self.processed_description.split()
                for b in processed_db_name.split()
            ]
        )

    def _full_word_number_of_letters_matching(self, processed_db_name: str) -> int:
        return sum(
            [
                len(self.str_processor(a).output)
                for a in self.processed_description.split()
                for b in processed_db_name.split()
                if self.str_processor(a).output == self.str_processor(b).output
            ]
        )

    def _full_word_positional_matching(self, processed_db_name: str) -> tuple[int, int]:
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
        return self._full_word_positional_matching(processed_db_name)[0]

    def _full_word_number_of_letters_with_positional_matching(
        self, processed_db_name: str
    ) -> int:
        return self._full_word_positional_matching(processed_db_name)[1]

    def _should_ignore(self, processed_db_name: str) -> bool:
        for word in self.words_that_must_fully_match:
            if re.compile(rf"\b{word}\b").search(processed_db_name) and not re.compile(
                rf"\b{word}\b"
            ).search(self.processed_description):
                return True
        return False

    @property
    def ranking(self):
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
        return [i for i in ranking if i.should_ignore is False]
