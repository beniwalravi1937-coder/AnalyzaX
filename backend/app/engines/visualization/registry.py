"""
Phase 9: Chart Support Tiers & Centralized Chart Type Registry (VIZ-T01 to VIZ-T10)
Single source of truth for chart tiers, capability contracts, and encoding rules.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChartTier(int, Enum):
    TIER_1_CORE = 1
    TIER_2_ADVANCED = 2
    TIER_3_SPECIALIZED = 3


class ChartTypeDefinition(BaseModel):
    """
    Central definition of a chart type in AnalyzaX.
    Determines tier, supported encodings, capability flags, and recommendation priority.
    """
    chart_type: str
    tier: ChartTier
    display_name: str
    description: str
    family: str  # "Comparison", "Trend", "Distribution", "Composition", "Relationship", "Summary", "Specialized"
    supported_encodings: List[str] = Field(default_factory=list)
    required_encodings: List[str] = Field(default_factory=list)
    optional_encodings: List[str] = Field(default_factory=list)
    supported_data_types: List[str] = Field(default_factory=list)
    supported_intents: List[str] = Field(default_factory=list)
    max_recommended_cardinality: Optional[int] = None
    supports_filters: bool = True
    supports_selection: bool = True
    supports_zoom: bool = False
    supports_drilldown: bool = True
    supports_export: bool = True
    supports_table_view: bool = True
    recommendation_priority: int = 50  # 1-100, higher = preferred within same suitability
    is_supported: bool = True  # False for deferred Tier 3


# ─────────────────────────────────────────────────────────────────────────────
# CENTRAL CHART TYPE REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

CHART_REGISTRY: Dict[str, ChartTypeDefinition] = {
    # ── TIER 1: CORE PRODUCTION CHARTS ───────────────────────────────────────
    "bar": ChartTypeDefinition(
        chart_type="bar",
        tier=ChartTier.TIER_1_CORE,
        display_name="Bar Chart",
        description="Category comparison and ranking with vertical bars",
        family="Comparison",
        required_encodings=["x", "y"],
        optional_encodings=["color", "series", "tooltip"],
        supported_encodings=["x", "y", "color", "series", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison", "ranking"],
        max_recommended_cardinality=30,
        supports_zoom=True,
        recommendation_priority=95,
    ),
    "horizontal_bar": ChartTypeDefinition(
        chart_type="horizontal_bar",
        tier=ChartTier.TIER_1_CORE,
        display_name="Horizontal Bar",
        description="Category comparison for many categories or long category labels",
        family="Comparison",
        required_encodings=["x", "y"],
        optional_encodings=["color", "series", "tooltip"],
        supported_encodings=["x", "y", "color", "series", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison", "ranking"],
        max_recommended_cardinality=50,
        supports_zoom=True,
        recommendation_priority=90,
    ),
    "grouped_bar": ChartTypeDefinition(
        chart_type="grouped_bar",
        tier=ChartTier.TIER_1_CORE,
        display_name="Grouped Bar",
        description="Comparing multiple measures or series side-by-side across categories",
        family="Comparison",
        required_encodings=["x", "y", "series"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "series", "color", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison"],
        max_recommended_cardinality=20,
        supports_zoom=True,
        recommendation_priority=85,
    ),
    "stacked_bar": ChartTypeDefinition(
        chart_type="stacked_bar",
        tier=ChartTier.TIER_1_CORE,
        display_name="Stacked Bar",
        description="Composition and absolute part-to-whole comparison across categories",
        family="Comparison",
        required_encodings=["x", "y", "series"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "series", "color", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["composition", "comparison"],
        max_recommended_cardinality=20,
        supports_zoom=True,
        recommendation_priority=80,
    ),
    "percent_stacked_bar": ChartTypeDefinition(
        chart_type="percent_stacked_bar",
        tier=ChartTier.TIER_1_CORE,
        display_name="100% Stacked Bar",
        description="Relative percentage composition across categories",
        family="Comparison",
        required_encodings=["x", "y", "series"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "series", "color", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["composition"],
        max_recommended_cardinality=20,
        supports_zoom=True,
        recommendation_priority=75,
    ),
    "line": ChartTypeDefinition(
        chart_type="line",
        tier=ChartTier.TIER_1_CORE,
        display_name="Line Chart",
        description="Continuous trends over temporal or sequential intervals",
        family="Trend",
        required_encodings=["x", "y"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["datetime", "numeric"],
        supported_intents=["trend"],
        supports_zoom=True,
        recommendation_priority=95,
    ),
    "multi_line": ChartTypeDefinition(
        chart_type="multi_line",
        tier=ChartTier.TIER_1_CORE,
        display_name="Multi-Series Line",
        description="Comparing multiple trends simultaneously over time",
        family="Trend",
        required_encodings=["x", "y", "series"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "series", "color", "tooltip"],
        supported_data_types=["datetime", "numeric", "categorical"],
        supported_intents=["trend", "comparison"],
        supports_zoom=True,
        recommendation_priority=90,
    ),
    "area": ChartTypeDefinition(
        chart_type="area",
        tier=ChartTier.TIER_1_CORE,
        display_name="Area Chart",
        description="Volume trends and cumulative magnitude over time",
        family="Trend",
        required_encodings=["x", "y"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["datetime", "numeric"],
        supported_intents=["trend"],
        supports_zoom=True,
        recommendation_priority=80,
    ),
    "stacked_area": ChartTypeDefinition(
        chart_type="stacked_area",
        tier=ChartTier.TIER_1_CORE,
        display_name="Stacked Area",
        description="Composition changes and aggregate volume trends over time",
        family="Trend",
        required_encodings=["x", "y", "series"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "series", "color", "tooltip"],
        supported_data_types=["datetime", "numeric", "categorical"],
        supported_intents=["trend", "composition"],
        supports_zoom=True,
        recommendation_priority=75,
    ),
    "scatter": ChartTypeDefinition(
        chart_type="scatter",
        tier=ChartTier.TIER_1_CORE,
        display_name="Scatter Plot",
        description="Relationships, correlation, and clustering between two continuous numeric variables",
        family="Relationship",
        required_encodings=["x", "y"],
        optional_encodings=["color", "series", "tooltip"],
        supported_encodings=["x", "y", "color", "series", "tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["relationship", "correlation"],
        supports_zoom=True,
        recommendation_priority=90,
    ),
    "histogram": ChartTypeDefinition(
        chart_type="histogram",
        tier=ChartTier.TIER_1_CORE,
        display_name="Histogram",
        description="Binned distribution and frequency of a single continuous numeric column",
        family="Distribution",
        required_encodings=["x"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "color", "tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["distribution"],
        supports_zoom=True,
        recommendation_priority=95,
    ),
    "box": ChartTypeDefinition(
        chart_type="box",
        tier=ChartTier.TIER_1_CORE,
        display_name="Box Plot",
        description="Five-number statistical summary (min, Q1, median, Q3, max) and outlier detection",
        family="Distribution",
        required_encodings=["y"],
        optional_encodings=["x", "color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["numeric", "categorical"],
        supported_intents=["distribution", "comparison"],
        supports_zoom=True,
        recommendation_priority=85,
    ),
    "heatmap": ChartTypeDefinition(
        chart_type="heatmap",
        tier=ChartTier.TIER_1_CORE,
        display_name="Heatmap",
        description="Density, intensity, or cross-tabulation matrix across two discrete dimensions",
        family="Relationship",
        required_encodings=["x", "y"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["relationship", "correlation"],
        max_recommended_cardinality=30,
        supports_zoom=True,
        recommendation_priority=80,
    ),
    "correlation_matrix": ChartTypeDefinition(
        chart_type="correlation_matrix",
        tier=ChartTier.TIER_1_CORE,
        display_name="Correlation Matrix",
        description="Pairwise Pearson/Spearman correlation coefficients across multiple numerical variables",
        family="Relationship",
        required_encodings=[],
        optional_encodings=["tooltip"],
        supported_encodings=["tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["correlation"],
        supports_zoom=True,
        recommendation_priority=85,
    ),
    "table": ChartTypeDefinition(
        chart_type="table",
        tier=ChartTier.TIER_1_CORE,
        display_name="Data Table",
        description="Exact numerical inspection, sorting, and tabular auditing",
        family="Summary",
        required_encodings=[],
        optional_encodings=["x", "y", "series"],
        supported_encodings=["x", "y", "series"],
        supported_data_types=["categorical", "numeric", "datetime"],
        supported_intents=["summary"],
        supports_zoom=False,
        recommendation_priority=70,
    ),
    "kpi": ChartTypeDefinition(
        chart_type="kpi",
        tier=ChartTier.TIER_1_CORE,
        display_name="KPI Metric Card",
        description="Single summary metric value with optional trend indicator",
        family="Summary",
        required_encodings=["y"],
        optional_encodings=["x", "tooltip"],
        supported_encodings=["x", "y", "tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["summary"],
        supports_zoom=False,
        recommendation_priority=75,
    ),

    # ── TIER 2: ADVANCED ANALYTICAL CHARTS ──────────────────────────────────
    "violin": ChartTypeDefinition(
        chart_type="violin",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Violin Plot",
        description="Kernel density estimation combined with box plot for multimodal distributions",
        family="Distribution",
        required_encodings=["y"],
        optional_encodings=["x", "color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["numeric", "categorical"],
        supported_intents=["distribution"],
        recommendation_priority=60,
    ),
    "ecdf": ChartTypeDefinition(
        chart_type="ecdf",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="ECDF Plot",
        description="Empirical Cumulative Distribution Function for percentile analysis without binning bias",
        family="Distribution",
        required_encodings=["x"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "color", "tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["distribution"],
        recommendation_priority=55,
    ),
    "density": ChartTypeDefinition(
        chart_type="density",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Density Plot",
        description="Continuous kernel density estimation curve of a numeric distribution",
        family="Distribution",
        required_encodings=["x"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "color", "tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["distribution"],
        recommendation_priority=55,
    ),
    "bubble": ChartTypeDefinition(
        chart_type="bubble",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Bubble Chart",
        description="Three-variable relationship where bubble area encodes a 3rd quantitative measure",
        family="Relationship",
        required_encodings=["x", "y", "size"],
        optional_encodings=["color", "series", "tooltip"],
        supported_encodings=["x", "y", "size", "color", "series", "tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["relationship"],
        supports_zoom=True,
        recommendation_priority=65,
    ),
    "treemap": ChartTypeDefinition(
        chart_type="treemap",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Treemap",
        description="Hierarchical part-to-whole composition using nested rectangles",
        family="Composition",
        required_encodings=["x", "y"],
        optional_encodings=["series", "tooltip"],
        supported_encodings=["x", "y", "series", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["composition"],
        max_recommended_cardinality=40,
        recommendation_priority=65,
    ),
    "donut": ChartTypeDefinition(
        chart_type="donut",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Donut Chart",
        description="Small part-to-whole comparisons strictly for 2 to 7 categories",
        family="Composition",
        required_encodings=["x", "y"],
        optional_encodings=["tooltip"],
        supported_encodings=["x", "y", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["composition"],
        max_recommended_cardinality=7,
        recommendation_priority=50,
    ),
    "pie": ChartTypeDefinition(
        chart_type="pie",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Pie Chart",
        description="Limited part-to-whole representation for low cardinality slices",
        family="Composition",
        required_encodings=["x", "y"],
        optional_encodings=["tooltip"],
        supported_encodings=["x", "y", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["composition"],
        max_recommended_cardinality=7,
        recommendation_priority=40,
    ),
    "pareto": ChartTypeDefinition(
        chart_type="pareto",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Pareto Chart",
        description="Combined bar and cumulative line identifying the 80/20 rule of contributions",
        family="Comparison",
        required_encodings=["x", "y"],
        optional_encodings=["tooltip"],
        supported_encodings=["x", "y", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison", "ranking"],
        recommendation_priority=60,
    ),
    "funnel": ChartTypeDefinition(
        chart_type="funnel",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Funnel Chart",
        description="Sequential stages in a linear process showing attrition and conversion rates",
        family="Specialized",
        required_encodings=["x", "y"],
        optional_encodings=["tooltip"],
        supported_encodings=["x", "y", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison"],
        recommendation_priority=50,
    ),
    "waterfall": ChartTypeDefinition(
        chart_type="waterfall",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Waterfall Chart",
        description="Sequential positive and negative cumulative contributions leading to a total",
        family="Specialized",
        required_encodings=["x", "y"],
        optional_encodings=["tooltip"],
        supported_encodings=["x", "y", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison"],
        recommendation_priority=50,
    ),
    "lollipop": ChartTypeDefinition(
        chart_type="lollipop",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Lollipop Chart",
        description="Compact category ranking reducing visual weight compared to standard bars",
        family="Comparison",
        required_encodings=["x", "y"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison", "ranking"],
        recommendation_priority=55,
    ),
    "dot_plot": ChartTypeDefinition(
        chart_type="dot_plot",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Dot Plot",
        description="Clean category comparison using markers on a common quantitative scale",
        family="Comparison",
        required_encodings=["x", "y"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison"],
        recommendation_priority=50,
    ),
    "ridgeline": ChartTypeDefinition(
        chart_type="ridgeline",
        tier=ChartTier.TIER_2_ADVANCED,
        display_name="Ridgeline Plot",
        description="Staggered partially overlapping density distributions across multiple categories",
        family="Distribution",
        required_encodings=["x", "series"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "series", "color", "tooltip"],
        supported_data_types=["numeric", "categorical"],
        supported_intents=["distribution"],
        recommendation_priority=45,
    ),

    # ── TIER 3: SPECIALIZED / EXTENSIBLE CHARTS (ARCHITECTURE / CONTRACT) ───
    "geographic_map": ChartTypeDefinition(
        chart_type="geographic_map",
        tier=ChartTier.TIER_3_SPECIALIZED,
        display_name="Geographic Map",
        description="Spatial geospatial point coordinates or boundary mapping",
        family="Specialized",
        required_encodings=["x", "y"],
        optional_encodings=["size", "color", "tooltip"],
        supported_encodings=["x", "y", "size", "color", "tooltip"],
        supported_data_types=["numeric", "categorical"],
        supported_intents=["relationship"],
        is_supported=False,
        recommendation_priority=10,
    ),
    "choropleth": ChartTypeDefinition(
        chart_type="choropleth",
        tier=ChartTier.TIER_3_SPECIALIZED,
        display_name="Choropleth Map",
        description="Regional shading based on an aggregated statistical measure",
        family="Specialized",
        required_encodings=["x", "y"],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["x", "y", "color", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison"],
        is_supported=False,
        recommendation_priority=10,
    ),
    "sankey": ChartTypeDefinition(
        chart_type="sankey",
        tier=ChartTier.TIER_3_SPECIALIZED,
        display_name="Sankey Diagram",
        description="Flows and multi-stage quantity transfers between categorical nodes",
        family="Specialized",
        required_encodings=["x", "y", "size"],
        optional_encodings=["tooltip"],
        supported_encodings=["x", "y", "size", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["relationship"],
        is_supported=False,
        recommendation_priority=15,
    ),
    "radar": ChartTypeDefinition(
        chart_type="radar",
        tier=ChartTier.TIER_3_SPECIALIZED,
        display_name="Radar Chart",
        description="Multi-attribute radial comparison across multiple quantitative dimensions",
        family="Specialized",
        required_encodings=["x", "y"],
        optional_encodings=["series", "tooltip"],
        supported_encodings=["x", "y", "series", "tooltip"],
        supported_data_types=["categorical", "numeric"],
        supported_intents=["comparison"],
        is_supported=False,
        recommendation_priority=15,
    ),
    "candlestick": ChartTypeDefinition(
        chart_type="candlestick",
        tier=ChartTier.TIER_3_SPECIALIZED,
        display_name="Candlestick / OHLC",
        description="Financial price movements with open, high, low, close intervals",
        family="Specialized",
        required_encodings=["x", "y"],
        optional_encodings=["tooltip"],
        supported_encodings=["x", "y", "tooltip"],
        supported_data_types=["datetime", "numeric"],
        supported_intents=["trend"],
        is_supported=False,
        recommendation_priority=10,
    ),
    "gantt": ChartTypeDefinition(
        chart_type="gantt",
        tier=ChartTier.TIER_3_SPECIALIZED,
        display_name="Gantt Timeline",
        description="Activity scheduling and duration tracking along a temporal baseline",
        family="Specialized",
        required_encodings=["x", "y"],
        optional_encodings=["series", "tooltip"],
        supported_encodings=["x", "y", "series", "tooltip"],
        supported_data_types=["datetime", "categorical"],
        supported_intents=["trend"],
        is_supported=False,
        recommendation_priority=10,
    ),
    "parallel_coordinates": ChartTypeDefinition(
        chart_type="parallel_coordinates",
        tier=ChartTier.TIER_3_SPECIALIZED,
        display_name="Parallel Coordinates",
        description="High-dimensional multivariate profile analysis across parallel vertical axes",
        family="Specialized",
        required_encodings=[],
        optional_encodings=["color", "tooltip"],
        supported_encodings=["color", "tooltip"],
        supported_data_types=["numeric"],
        supported_intents=["relationship"],
        is_supported=False,
        recommendation_priority=5,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY HELPER FUNCTIONS (VIZ-T08, VIZ-T10)
# ─────────────────────────────────────────────────────────────────────────────

def get_chart_definition(chart_type: Any) -> Optional[ChartTypeDefinition]:
    """Retrieve chart type definition from central registry."""
    if not chart_type:
        return None
    if hasattr(chart_type, "value"):
        key = str(chart_type.value)
    else:
        key = str(chart_type)
    if "." in key:
        key = key.split(".")[-1]
    normalized = key.lower().strip()
    if normalized == "boxplot":
        normalized = "box"
    elif normalized == "kpi_card":
        normalized = "kpi"
    return CHART_REGISTRY.get(normalized)


def list_charts_by_tier(tier: ChartTier) -> List[ChartTypeDefinition]:
    """List all charts belonging to a specific tier."""
    return [def_ for def_ in CHART_REGISTRY.values() if def_.tier == tier]


def is_chart_supported(chart_type: str) -> bool:
    """Check whether a chart type is production-supported in Phase 9."""
    definition = get_chart_definition(chart_type)
    return definition is not None and definition.is_supported


def get_tier(chart_type: str) -> Optional[ChartTier]:
    """Get the tier of a chart type."""
    definition = get_chart_definition(chart_type)
    return definition.tier if definition else None
