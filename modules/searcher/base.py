"""搜索结果统一数据模型和基类"""
from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod


@dataclass
class Paper:
    title: str
    authors: list[str]
    year: Optional[int]
    journal: Optional[str]
    doi: Optional[str]
    abstract: Optional[str]
    citation_count: Optional[int] = None
    url: Optional[str] = None
    source: str = ""  # 数据来源标识

    @property
    def doi_url(self) -> Optional[str]:
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return self.url

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "doi_url": self.doi_url,
            "abstract": self.abstract,
            "citation_count": self.citation_count,
            "source": self.source,
        }

    def __str__(self) -> str:
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        return f"{authors_str}. {self.title}. {self.journal or 'N/A'}, {self.year or 'N/A'}. DOI: {self.doi or 'N/A'}"


class BaseSearcher(ABC):
    """搜索引擎基类"""

    source_name: str = "unknown"

    @abstractmethod
    def search(self, query: str, year_start: int = 2021, year_end: int = 2026, limit: int = 10) -> list[Paper]:
        ...
