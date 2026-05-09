"""Transaction management utilities for database operations."""

import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database transactions.

    Automatically commits on successful completion and rolls back on exceptions.

    Args:
        session: Async SQLAlchemy session

    Yields:
        The session within a transaction context

    Example:
        async with transaction(db) as tx:
            await tx.execute(update(...))
            await tx.commit()  # Optional - auto-commits
    """
    try:
        await session.begin()
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise


@asynccontextmanager
async def nested_transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Context manager for nested transactions (savepoints).

    Uses savepoints to allow partial rollback within a larger transaction.

    Args:
        session: Async SQLAlchemy session

    Yields:
        The session within a savepoint context

    Example:
        async with transaction(db) as tx:
            async with nested_transaction(tx) as nested:
                # Operations here can be rolled back independently
    """
    try:
        await session.begin_nested()
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Nested transaction rolled back: {e}")
        raise


async def with_retry(
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    retry_exceptions: tuple[type[Exception], ...] | None = None,
    delay: float = 0.1,
) -> T:
    """Execute a function with retry logic for transient failures.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        retry_exceptions: Tuple of exception types to retry on (default: all)
        delay: Initial delay between retries in seconds (exponential backoff)

    Returns:
        The result of the function

    Raises:
        The last exception if all retries are exhausted

    Example:
        result = await with_retry(
            lambda: create_document(db, data),
            max_retries=3,
            retry_exceptions=(OperationalError, TimeoutError),
        )
    """
    import asyncio
    import random

    if retry_exceptions is None:
        retry_exceptions = (Exception,)

    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retry_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                # Exponential backoff with jitter
                backoff = delay * (2**attempt) + random.uniform(0, 0.1)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {backoff:.2f}s..."
                )
                await asyncio.sleep(backoff)

    logger.error(f"All {max_retries + 1} attempts failed")
    if last_exception is not None:
        raise last_exception
    raise RuntimeError("All retry attempts failed with no exception captured")


async def execute_in_batches(
    items: list[Any],
    batch_size: int,
    processor: Callable[[list[Any]], Awaitable[None]],
) -> None:
    """Execute a processor function on items in batches.

    Useful for bulk operations that need to be broken into smaller chunks
    to avoid memory issues or database timeouts.

    Args:
        items: List of items to process
        batch_size: Number of items per batch
        processor: Async function that processes a batch

    Example:
        await execute_in_batches(
            document_ids,
            batch_size=100,
            processor=lambda batch: bulk_update_documents(db, batch),
        )
    """
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        logger.debug(f"Processing batch {i // batch_size + 1}: {len(batch)} items")
        await processor(batch)


class TransactionError(Exception):
    """Raised when a transaction operation fails."""

    def __init__(self, message: str, operation: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.operation = operation
