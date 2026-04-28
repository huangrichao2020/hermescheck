"""Scanner registry and exports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from hermescheck.config import AuditConfig
from hermescheck.scanners.bug_inference import scan_bug_inference
from hermescheck.scanners.capability_policy import scan_capability_policy
from hermescheck.scanners.code_execution import scan_code_execution
from hermescheck.scanners.completion_closure import scan_completion_closure
from hermescheck.scanners.daemon_lifecycle import scan_daemon_lifecycle
from hermescheck.scanners.excessive_agency import scan_excessive_agency
from hermescheck.scanners.hermes_contract import scan_hermes_contract
from hermescheck.scanners.hidden_llm import scan_hidden_llm_calls
from hermescheck.scanners.impression_memory import scan_impression_memory
from hermescheck.scanners.internal_orchestration import scan_internal_orchestration
from hermescheck.scanners.loop_safety import scan_loop_safety
from hermescheck.scanners.memory_freshness import scan_memory_freshness
from hermescheck.scanners.memory_lifecycle import scan_memory_lifecycle
from hermescheck.scanners.memory_patterns import scan_memory_patterns
from hermescheck.scanners.memory_retrieval_i18n import scan_memory_retrieval_i18n
from hermescheck.scanners.observability import scan_observability
from hermescheck.scanners.os_architecture import scan_os_architecture
from hermescheck.scanners.output_pipeline import scan_output_pipeline
from hermescheck.scanners.pipeline_middleware_integrity import scan_pipeline_middleware_integrity
from hermescheck.scanners.plugin_execution_policy import scan_plugin_execution_policy
from hermescheck.scanners.rag_pipeline_governance import scan_rag_pipeline_governance
from hermescheck.scanners.role_play_orchestration import scan_role_play_orchestration
from hermescheck.scanners.runtime_complexity import scan_runtime_complexity
from hermescheck.scanners.secrets import scan_secrets
from hermescheck.scanners.self_evolution_capability import scan_self_evolution_capability
from hermescheck.scanners.skill_duplication import scan_skill_duplication
from hermescheck.scanners.startup_complexity import scan_startup_complexity
from hermescheck.scanners.token_usage import scan_token_usage
from hermescheck.scanners.tool_enforcement import scan_tool_enforcement
from hermescheck.scanners.tool_server_boundary import scan_tool_server_boundary

ScannerFunc = Callable[[Path, AuditConfig], List[dict]]


@dataclass(frozen=True)
class ScannerSpec:
    slug: str
    name: str
    func: ScannerFunc
    audited_layers: tuple[str, ...]


def _adapt(scan_fn: Callable[[Path], List[dict]]) -> ScannerFunc:
    return lambda target, config: scan_fn(target)


SCANNER_REGISTRY = [
    ScannerSpec(
        slug="hermes_contract",
        name="Hermes Agent Runtime Contract",
        func=_adapt(scan_hermes_contract),
        audited_layers=("hermes_runtime_contract", "hermes_command_registry"),
    ),
    ScannerSpec(
        slug="secrets",
        name="Hardcoded Secrets",
        func=_adapt(scan_secrets),
        audited_layers=("persistence",),
    ),
    ScannerSpec(
        slug="internal_orchestration",
        name="Internal Orchestration Sprawl",
        func=_adapt(scan_internal_orchestration),
        audited_layers=("tool_selection", "fallback_loops"),
    ),
    ScannerSpec(
        slug="completion_closure",
        name="Completion Closure Gap",
        func=_adapt(scan_completion_closure),
        audited_layers=("completion_closure", "active_recall"),
    ),
    ScannerSpec(
        slug="bug_inference",
        name="Static Bug Inference",
        func=_adapt(scan_bug_inference),
        audited_layers=("runtime_bug_inference", "platform_rendering", "tool_execution"),
    ),
    ScannerSpec(
        slug="token_usage",
        name="Token Usage Budget",
        func=_adapt(scan_token_usage),
        audited_layers=("token_usage", "session_history", "long_term_memory", "active_recall"),
    ),
    ScannerSpec(
        slug="memory_freshness",
        name="Memory Freshness Confusion",
        func=_adapt(scan_memory_freshness),
        audited_layers=("session_history", "long_term_memory"),
    ),
    ScannerSpec(
        slug="memory_lifecycle",
        name="Memory Lifecycle Governance",
        func=_adapt(scan_memory_lifecycle),
        audited_layers=("long_term_memory", "active_recall"),
    ),
    ScannerSpec(
        slug="memory_retrieval_i18n",
        name="Memory Retrieval I18N",
        func=_adapt(scan_memory_retrieval_i18n),
        audited_layers=("long_term_memory", "active_recall"),
    ),
    ScannerSpec(
        slug="rag_pipeline_governance",
        name="RAG Pipeline Governance",
        func=_adapt(scan_rag_pipeline_governance),
        audited_layers=("long_term_memory", "active_recall", "knowledge_retrieval"),
    ),
    ScannerSpec(
        slug="self_evolution_capability",
        name="Self-Evolution Capability",
        func=_adapt(scan_self_evolution_capability),
        audited_layers=("self_evolution", "active_recall", "persistence"),
    ),
    ScannerSpec(
        slug="impression_memory",
        name="Impression Pointer Memory",
        func=_adapt(scan_impression_memory),
        audited_layers=("impression_memory", "active_recall"),
    ),
    ScannerSpec(
        slug="role_play_orchestration",
        name="Role-Play Handoff Orchestration",
        func=_adapt(scan_role_play_orchestration),
        audited_layers=("tool_selection", "fallback_loops"),
    ),
    ScannerSpec(
        slug="os_architecture",
        name="Agent OS Architecture",
        func=_adapt(scan_os_architecture),
        audited_layers=("os_memory", "os_scheduler", "os_syscall", "os_vfs", "stateful_recovery", "llm_cli_workers"),
    ),
    ScannerSpec(
        slug="daemon_lifecycle",
        name="Daemon Lifecycle Safety",
        func=_adapt(scan_daemon_lifecycle),
        audited_layers=("persistence", "os_scheduler", "stateful_recovery"),
    ),
    ScannerSpec(
        slug="capability_policy",
        name="Capability Permission Policy",
        func=_adapt(scan_capability_policy),
        audited_layers=("tool_selection", "tool_execution", "os_syscall"),
    ),
    ScannerSpec(
        slug="plugin_execution_policy",
        name="Plugin Execution Policy",
        func=_adapt(scan_plugin_execution_policy),
        audited_layers=("tool_selection", "tool_execution", "plugin_execution"),
    ),
    ScannerSpec(
        slug="tool_server_boundary",
        name="Remote Tool Server Boundary",
        func=_adapt(scan_tool_server_boundary),
        audited_layers=("tool_selection", "tool_execution", "remote_tools"),
    ),
    ScannerSpec(
        slug="pipeline_middleware_integrity",
        name="Pipeline Middleware Integrity",
        func=_adapt(scan_pipeline_middleware_integrity),
        audited_layers=("answer_shaping", "tool_execution", "pipeline_middleware"),
    ),
    ScannerSpec(
        slug="skill_duplication",
        name="Skill Duplication",
        func=_adapt(scan_skill_duplication),
        audited_layers=("active_recall", "persistence"),
    ),
    ScannerSpec(
        slug="startup_complexity",
        name="Startup Surface Sprawl",
        func=_adapt(scan_startup_complexity),
        audited_layers=("platform_rendering", "persistence"),
    ),
    ScannerSpec(
        slug="runtime_complexity",
        name="Runtime Surface Sprawl",
        func=_adapt(scan_runtime_complexity),
        audited_layers=("platform_rendering", "persistence"),
    ),
    ScannerSpec(
        slug="tool_enforcement",
        name="Tool Enforcement Gap",
        func=_adapt(scan_tool_enforcement),
        audited_layers=("tool_selection", "tool_execution"),
    ),
    ScannerSpec(
        slug="hidden_llm",
        name="Hidden LLM Calls",
        func=_adapt(scan_hidden_llm_calls),
        audited_layers=("fallback_loops", "tool_selection"),
    ),
    ScannerSpec(
        slug="code_execution",
        name="Unrestricted Code Execution",
        func=_adapt(scan_code_execution),
        audited_layers=("tool_execution",),
    ),
    ScannerSpec(
        slug="memory_patterns",
        name="Memory Pattern Issues",
        func=_adapt(scan_memory_patterns),
        audited_layers=("session_history", "long_term_memory"),
    ),
    ScannerSpec(
        slug="output_pipeline",
        name="Output Pipeline Mutation",
        func=_adapt(scan_output_pipeline),
        audited_layers=("answer_shaping", "platform_rendering"),
    ),
    ScannerSpec(
        slug="observability",
        name="Missing Observability",
        func=_adapt(scan_observability),
        audited_layers=("persistence",),
    ),
    ScannerSpec(
        slug="excessive_agency",
        name="Excessive Agency",
        func=scan_excessive_agency,
        audited_layers=("tool_selection", "tool_execution"),
    ),
]


def get_enabled_scanners(config: AuditConfig) -> list[ScannerSpec]:
    if config.enabled_scanners:
        enabled = [spec for spec in SCANNER_REGISTRY if spec.slug in config.enabled_scanners]
    else:
        enabled = list(SCANNER_REGISTRY)

    if config.profile.key == "personal_development":
        personal_priority = [
            "hermes_contract",
            "internal_orchestration",
            "completion_closure",
            "bug_inference",
            "token_usage",
            "memory_freshness",
            "memory_lifecycle",
            "memory_retrieval_i18n",
            "rag_pipeline_governance",
            "self_evolution_capability",
            "impression_memory",
            "role_play_orchestration",
            "os_architecture",
            "daemon_lifecycle",
            "capability_policy",
            "plugin_execution_policy",
            "tool_server_boundary",
            "pipeline_middleware_integrity",
            "skill_duplication",
            "startup_complexity",
            "runtime_complexity",
            "memory_patterns",
            "hidden_llm",
            "tool_enforcement",
            "output_pipeline",
            "code_execution",
            "observability",
            "secrets",
            "excessive_agency",
        ]
        order = {slug: index for index, slug in enumerate(personal_priority)}
        enabled.sort(key=lambda spec: order.get(spec.slug, len(order)))

    return enabled


__all__ = [
    "ScannerSpec",
    "SCANNER_REGISTRY",
    "get_enabled_scanners",
    "scan_bug_inference",
    "scan_capability_policy",
    "scan_code_execution",
    "scan_completion_closure",
    "scan_daemon_lifecycle",
    "scan_excessive_agency",
    "scan_hermes_contract",
    "scan_hidden_llm_calls",
    "scan_impression_memory",
    "scan_internal_orchestration",
    "scan_loop_safety",
    "scan_memory_freshness",
    "scan_memory_lifecycle",
    "scan_memory_patterns",
    "scan_memory_retrieval_i18n",
    "scan_observability",
    "scan_os_architecture",
    "scan_output_pipeline",
    "scan_pipeline_middleware_integrity",
    "scan_plugin_execution_policy",
    "scan_rag_pipeline_governance",
    "scan_role_play_orchestration",
    "scan_runtime_complexity",
    "scan_secrets",
    "scan_self_evolution_capability",
    "scan_skill_duplication",
    "scan_startup_complexity",
    "scan_token_usage",
    "scan_tool_enforcement",
    "scan_tool_server_boundary",
]
