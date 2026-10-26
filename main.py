import logging
from logger import setup_logging
from domain.value_objects import ColumnType, ChartRule, ChartType, ChartConditions
from domain.interfaces import IDataLoader, IColumnTypeDetector, IStatisticCalculator, IChartRuleEngine, IChartRenderer, IReportExporter
from application.dto import DatasetInfoDTO, AnalysisResultDTO
from application.services.data_service import DataService
from application.services.analysis_service import AnalysisService
from application.services.chart_builder_service import ChartBuilderService
from application.services.report_service import ReportService
from application.services.aggregation_service import AggregationService

setup_logging()
logger = logging.getLogger(__name__)
data = [
   {"date": "2024-01-01", "category": "A", "value": 100, "score": 5},
   {"date": "2024-01-02", "category": "B", "value": 200, "score": 7},
   {"date": "2024-01-03", "category": "A", "value": 150, "score": 6},
]
class L(IDataLoader):
   def load(self, s, **kw): return data
class D(IColumnTypeDetector):
   def detect(self, d): return {k: ColumnType.DATE if "date" in k else ColumnType.CATEGORICAL if "cat" in k else ColumnType.NUMERIC for k in d[0]}
class S(IStatisticCalculator):
   def calculate(self, d, ct): return ({c: {"min": min(r[c] for r in d), "max": max(r[c] for r in d)} for c in ct}, None)
class E(IChartRuleEngine):
   def apply(self, ct, rules): return sorted(rules, key=lambda r: -r.priority)
class R(IChartRenderer):
   def render(self, c): return f"rendered:{c.chart_id}"
   def export_dashboard_to_html(self, cs, p): return p
class X(IReportExporter):
   def export(self, rd, p): return p
ds, a, cb, rp = DataService({".csv": L()}), AnalysisService(D(), S()), ChartBuilderService(E()), ReportService(X(), R(), X())
loaded = ds.load_data("test/test.csv")
profile = a.analyze_dataset(loaded)
suggested = cb.build_suggested_charts(profile, loaded)
result = AnalysisResultDTO(DatasetInfoDTO("test/test.csv", profile.row_count, profile.column_count, "test.csv"), profile, suggested)
logger.info(f"rows={len(loaded)} cols={profile.column_count} charts={len(suggested)}")
[logger.info(f"  {c.chart_type.value}: {c.title}") for c in suggested]
logger.info(f"freq={AggregationService.frequency(loaded, 'category')}")
logger.info(f"ws={AggregationService.weighted_sum(loaded, 'value', 'score')}")
logger.info(f"wa={AggregationService.weighted_avg(loaded, 'value', 'score')}")
logger.info(f"report={rp.create_report(result, 'out.docx')}")