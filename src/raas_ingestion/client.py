from typing import Any, Callable, Optional
from .auth import TokenManager
from .paginator import PaginatedResult, RaaSPaginator
from .retry_policy import RetryConfig, execute_with_retry


class WorkdayRaaSClient:
    """Coordinates authenticated, retried, paginated ingestion from Workday endpoints."""

    def __init__(
        self,
        token_manager: TokenManager,
        transport: Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]],
        retry_config: Optional[RetryConfig] = None,
        page_size: int = 100,
    ) -> None:
        self.token_manager = token_manager
        self.transport = transport
        self.retry_config = retry_config or RetryConfig()
        self.paginator = RaaSPaginator(page_size=page_size)

    def fetch_report(self, endpoint_url: str, extra_params: Optional[dict[str, Any]] = None) -> PaginatedResult:
        base_params = dict(extra_params or {})

        def fetch_page(offset: int, limit: int) -> dict[str, Any]:
            params = {**base_params, "offset": offset, "limit": limit, "format": "json"}

            def _call() -> dict[str, Any]:
                headers = self.token_manager.get_auth_header()
                return self.transport(endpoint_url, headers, params)

            return execute_with_retry(_call, config=self.retry_config)

        return self.paginator.collect_all_offset(fetch_page)
