from dataclasses import dataclass
from typing import Any, Callable, Iterator


@dataclass
class PaginatedResult:
    records: list[dict[str, Any]]
    total_pages: int
    total_records: int


class RaaSPaginator:
    """Supports both offset-based and cursor-based Workday RaaS/REST pagination."""

    def __init__(self, page_size: int = 100, max_pages: int = 500) -> None:
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        self.page_size = page_size
        self.max_pages = max_pages

    def iter_offset_pages(
        self,
        fetch_page: Callable[[int, int], dict[str, Any]],
        data_key: str = "Report_Entry",
    ) -> Iterator[list[dict[str, Any]]]:
        offset = 0
        for _ in range(self.max_pages):
            payload = fetch_page(offset, self.page_size)
            batch = payload.get(data_key, [])
            if not batch:
                break
            yield batch
            if len(batch) < self.page_size:
                break
            offset += len(batch)

    def collect_all_offset(
        self,
        fetch_page: Callable[[int, int], dict[str, Any]],
        data_key: str = "Report_Entry",
    ) -> PaginatedResult:
        all_records: list[dict[str, Any]] = []
        pages = 0
        for batch in self.iter_offset_pages(fetch_page, data_key=data_key):
            pages += 1
            all_records.extend(batch)
        return PaginatedResult(records=all_records, total_pages=pages, total_records=len(all_records))
