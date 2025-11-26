"""Tests for Prometheus metrics utilities."""

from security_llm_lab.observability.metrics import CollectorRegistry, MetricsEmitter


def test_metrics_record_pipeline_run_updates_counters():
    registry = CollectorRegistry()
    emitter = MetricsEmitter(enabled=True, registry=registry)

    emitter.record_pipeline_run(artifact_count=3, duration_seconds=1.2)

    assert registry.get_sample_value("security_llm_lab_pipeline_runs_total") == 1
    assert registry.get_sample_value("security_llm_lab_last_artifact_count") == 3
    # Summary creates _sum and _count samples
    duration_sum = registry.get_sample_value("security_llm_lab_pipeline_duration_seconds_sum")
    assert duration_sum and duration_sum > 0


def test_metrics_disabled_is_noop():
    registry = CollectorRegistry()
    emitter = MetricsEmitter(enabled=False, registry=registry)

    emitter.record_pipeline_run(artifact_count=1, duration_seconds=0.5)

    assert registry.get_sample_value("security_llm_lab_pipeline_runs_total") is None
    assert registry.get_sample_value("security_llm_lab_last_artifact_count") is None
