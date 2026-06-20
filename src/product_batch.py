
import re
from datetime import date


class ProductBatch:
    """
    Represents a traceable unit of agricultural produce.
    
    batch_id must follow pattern: NG-YYYY-XXXXXXXX
    where YYYY is a 4-digit year and XXXXXXXX is
    an 8-digit alphanumeric code.
    
    All weight attributes are validated to be
    positive numbers.
    """

    BATCH_ID_PATTERN = re.compile(
        r'^NG-\d{4}-[A-Z0-9]{8}$'
    )

    def __init__(self,
                 batch_id: str,
                 product_name: str,
                 category: str,
                 origin_farm: str,
                 harvest_date: date,
                 initial_weight_kg: float,
                 current_custodian):
        """
        Initialise a new ProductBatch.

        Args:
            batch_id: Unique ID in format NG-YYYY-XXXXXXXX
            product_name: Name of the product e.g. Rice
            category: Category e.g. Grains, Perishables
            origin_farm: Name of the farm of origin
            harvest_date: Date the produce was harvested
            initial_weight_kg: Starting weight in kg
            current_custodian: The SupplyChainActor
                               currently holding the batch
        """
        self.batch_id = batch_id
        self._product_name = product_name
        self._category = category
        self._origin_farm = origin_farm
        self._harvest_date = harvest_date
        self.initial_weight_kg = initial_weight_kg
        self._current_weight_kg = initial_weight_kg
        self._current_custodian = current_custodian

    # ── batch_id ──────────────────────────────────────
    @property
    def batch_id(self) -> str:
        """Return the batch ID."""
        return self.__batch_id

    @batch_id.setter
    def batch_id(self, value: str):
        """Validate and set the batch ID."""
        if not isinstance(value, str):
            raise TypeError(
                'batch_id must be a string.'
            )
        if not self.BATCH_ID_PATTERN.match(value):
            raise ValueError(
                f'Invalid batch_id: {value!r}. '
                f'Must match pattern NG-YYYY-XXXXXXXX '
                f'e.g. NG-2026-AB123456'
            )
        self.__batch_id = value

    # ── product_name ──────────────────────────────────
    @property
    def product_name(self) -> str:
        """Return the product name."""
        return self._product_name

    @product_name.setter
    def product_name(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                'product_name must be a non-empty string.'
            )
        self._product_name = value.strip()

    # ── category ──────────────────────────────────────
    @property
    def category(self) -> str:
        """Return the product category."""
        return self._category

    @category.setter
    def category(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                'category must be a non-empty string.'
            )
        self._category = value.strip()

    # ── origin_farm ───────────────────────────────────
    @property
    def origin_farm(self) -> str:
        """Return the origin farm name."""
        return self._origin_farm

    @origin_farm.setter
    def origin_farm(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                'origin_farm must be a non-empty string.'
            )
        self._origin_farm = value.strip()

    # ── harvest_date ──────────────────────────────────
    @property
    def harvest_date(self) -> date:
        """Return the harvest date."""
        return self._harvest_date

    @harvest_date.setter
    def harvest_date(self, value: date):
        if not isinstance(value, date):
            raise TypeError(
                'harvest_date must be a date object.'
            )
        if value > date.today():
            raise ValueError(
                'harvest_date cannot be in the future.'
            )
        self._harvest_date = value

    # ── initial_weight_kg ─────────────────────────────
    @property
    def initial_weight_kg(self) -> float:
        """Return the initial weight in kg."""
        return self._initial_weight_kg

    @initial_weight_kg.setter
    def initial_weight_kg(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError(
                'initial_weight_kg must be a number.'
            )
        if value <= 0:
            raise ValueError(
                'initial_weight_kg must be positive.'
            )
        self._initial_weight_kg = float(value)

    # ── current_weight_kg ─────────────────────────────
    @property
    def current_weight_kg(self) -> float:
        """Return the current weight in kg."""
        return self._current_weight_kg

    @current_weight_kg.setter
    def current_weight_kg(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError(
                'current_weight_kg must be a number.'
            )
        if value < 0:
            raise ValueError(
                'current_weight_kg cannot be negative.'
            )
        self._current_weight_kg = float(value)

    # ── current_custodian ─────────────────────────────
    @property
    def current_custodian(self):
        """Return the current custodian actor."""
        return self._current_custodian

    @current_custodian.setter
    def current_custodian(self, value):
        if value is None:
            raise ValueError(
                'current_custodian cannot be None.'
            )
        self._current_custodian = value

    # ── dunder methods ────────────────────────────────
    def __str__(self) -> str:
        return (
            f'ProductBatch({self.__batch_id}) | '
            f'{self._product_name} | '
            f'Category: {self._category} | '
            f'Farm: {self._origin_farm} | '
            f'Weight: {self._current_weight_kg}kg'
        )

    def __repr__(self) -> str:
        return (
            f'ProductBatch(batch_id={self.__batch_id!r}, '
            f'product_name={self._product_name!r}, '
            f'category={self._category!r}, '
            f'origin_farm={self._origin_farm!r}, '
            f'harvest_date={self._harvest_date!r}, '
            f'initial_weight_kg={self._initial_weight_kg!r})'
                   )
