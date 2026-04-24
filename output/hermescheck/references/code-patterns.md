# Code-Level Anti-Patterns

Concrete grep-searchable patterns to find agent wrapper failures in source code.

These patterns are auto-generated from the [hermescheck](https://github.com/huangrichao2020/hermescheck) Python scanners.
Each section lists the regex patterns used by that scanner.

## Usage

```bash
pip install hermescheck
hermescheck /path/to/your/agent/project
```

Or run individual grep scans manually:

## Code Execution

**Scanner file**: `hermescheck/scanners/code_execution.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?<!\.)\bexec\s*\(`
- `(?<!\.)\beval\s*\(`
- `(?<!\.)\bcompile\s*\(`
- `\bos\.system\s*\(`
- `\bnew\s+Function\s*\(`
- `subprocess\..*shell\s*=\s*True`
- `(?:sandbox|docker|container|seccomp|chroot|\bvm\b|`
- `subprocess.*timeout|resource\.setrlimit|jail|`
- `nsjail|firejail|gvisor|kata)`
- `: `

## Completion Closure

**Scanner file**: `hermescheck/scanners/completion_closure.py`

**Default severity**: `medium`

**Regex patterns**:

- `\b(?:create file|write file|save file|mkdir|touch|open\(.*[\`
- `\b(?:update index|index update|registry|manifest|catalog|toc|table of contents)\b|(?:更新索引|索引更新|目录|清单|注册表)`
- `\b(?:impression card|memory card|summary card|cue card|concept card)\b|(?:印象卡片|记忆卡片|概念卡片)`
- `\b(?:anchor mapping|semantic anchor|topic_anchor|anchor map|concept anchor)\b|(?:锚点映射|语义锚点|主题锚点)`
- `: re.compile(
        r`
- `\b(?:acceptance|acceptance criteria|done criteria|verify|validation|self[-_ ]?test|reusable|can find|next time)\b|(?:验收|验收标准|完成标准|验证|可复用|下次.*找到)`
- `\b(?:done|completed|task complete|finished|success)\b|(?:完成|已完成|任务完成|成功)`
- `, `
- `: `
- `: `

## Excessive Agency

**Scanner file**: `hermescheck/scanners/excessive_agency.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:subprocess\.run|subprocess\.Popen|os\.system|shell\s*=\s*True|`
- `\bexec\s*\(|\beval\s*\(|browser_control|playwright|selenium|`
- `requests\.(?:get|post|put|delete)|httpx\.(?:get|post|put|delete)|`
- `\bfetch\s*\(|axios\.(?:get|post|put|delete)|write_text\(|write_bytes\(|`
- `\.unlink\(|os\.remove\(|shutil\.rmtree\()`
- `(?:approve|approval|confirm|consent|require_approval|request_approval|`
- `user_confirm|human_in_the_loop|manual_review)`
- `(?:sandbox|docker|container|isolat|gvisor|nsjail|seccomp|read_only|`
- `readonly|resource\.setrlimit|timeout\s*=|network_disabled)`
- `(?:allowlist|whitelist|ALLOWED_|SAFE_COMMANDS|allowed_commands|`
- `allowed_paths|permitted_commands|permitted_paths)`
- `: `

## Hermes Contract

**Scanner file**: `hermescheck/scanners/hermes_contract.py`

**Default severity**: `high`

**Regex patterns**:

- `,
    `
- `: `
- `: `

## Hidden Llm

**Scanner file**: `hermescheck/scanners/hidden_llm.py`

**Default severity**: `high`

**Regex patterns**:

- `(?:chat(?:\.completions)?\.create|messages\.create|completions\.create|llm\.invoke|`
- `openai\.chat|anthropic\.messages|vertexai\.predict|`
- `bedrock.*invoke|model\.generate|completion\.create)\s*\(`
- `(?:fallback|repair|second.*pass|re-prompt|retry.*llm|judge.*llm|reflect.*llm)`
- `(?:agent.*loop|main.*loop|orchestrat|chain.*run|agent.*run|`
- `agent_executor|react.*loop|tool.*loop|cycle.*run)`
- `(?:provider|adapter|client_factory|model_backend|llm_gateway|client|gateway)`
- `(?:class\s+\w*Provider|def\s+\w*provider)`
- `: `
- `: `

## Impression Memory

**Scanner file**: `hermescheck/scanners/impression_memory.py`

**Default severity**: `medium`

**Regex patterns**:

- `\b(?:fact|facts|preference|preferences|profile|user profile|entity|entities|attribute|metadata)\b|(?:事实|偏好|画像|实体)`
- `\b(?:skill|skills|procedure|procedural|workflow|runbook|sop|playbook|capability)\b|(?:技能|流程|经验|操作手册)`
- `\b(?:session|conversation|dialogue|transcript|history|episode|event|memory chunk|chunk)\b|(?:会话|对话|片段|事件)`
- `\b(?:impression|impressions|associative|association|cue|gist|landmark|mental map|concept map|`
- `semantic hint|route hint|memory impression|impression chunk)\b|(?:印象|联想|概念路标|路标|线索|语义提示|大概知道)`
- `\b(?:pointer_ref|pointer_type|vector_id|file_path|skill_id|semantic_hash|semantic anchor|`
- `topic_anchor|page table|page entry|page fault|swap in|swap-in|activation_level|in_mind|subconscious|`
- `forgotten|retrieval pointer)\b|(?:语义锚点|页表|页表项|缺页|换入|激活层级|潜意识|遗忘)`
- `(?:impression|memory|page[_ -]?table|page[_ -]?fault|semantic[_ -]?hash|topic[_ -]?anchor|`
- `pointer[_ -]?(?:ref|type)|vector_id|activation_level|印象|记忆|页表|缺页|语义锚点)`
- `: [],
    }
    files = [target] if target.is_file() else sorted(target.rglob(`
- `].append(path_ref)

        try:
            lines = fp.read_text(encoding=`
- `].append(ref)
    return refs


def _evidence(refs: dict[str, list[str]]) -> list[str]:
    evidence_refs: list[str] = []
    seen: set[str] = set()
    for key in (`
- `):
        for ref in refs[key][:4]:
            if ref not in seen:
                evidence_refs.append(ref)
                seen.add(ref)
    return evidence_refs[:10]


def scan_impression_memory(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    has_memory_system = len(refs[`
- `]) >= 2

    if not has_memory_system or not has_skill_system:
        return []

    findings: List[Dict[str, Any]] = []
    if not has_impressions:
        findings.append(
            {
                `
- `: `
- `: `

## Internal Orchestration

**Scanner file**: `hermescheck/scanners/internal_orchestration.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:^|[^a-z])plan(?:ner|ning|_task|_step)?`
- `(?:route|router|dispatch|selector|handoff)`
- `(?:subagent|worker|delegate|swarm|team|multi[_ -]?agent)`
- `(?:schedule|scheduler|cron|heartbeat|timer)`
- `(?:retry|fallback|repair|reflect|judge|critic)`
- `: `

## Memory Freshness

**Scanner file**: `hermescheck/scanners/memory_freshness.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:memory|checkpoint|archive|summary|history|session|state|snapshot|insight)`
- `(?:^|[-_ ])(?:old|new|latest|final|draft|copy|backup|bak|v\d+)(?:$|[-_ ])`
- `[^a-z0-9]+`
- `: `

## Memory Patterns

**Scanner file**: `hermescheck/scanners/memory_patterns.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:memory.*admit|long.?term.*update|persist.*memory|save.*to.*memory|`
- `memory.*store|write.*memory|commit.*memory|memory.*insert)`
- `(?:add.*memory|upsert.*vector|append.*context|history.*append|`
- `messages.*append|memory.*push|context.*grow|buffer.*append|`
- `memory.*add|vector.*insert|embeddings.*store)`
- `(?:max_|limit|ttl|expire|k=|top_|threshold|trim|truncate|`
- `max_|_max|capacity|bounded|evict|prune|retention|window_size)`
- `: `

## Observability

**Scanner file**: `hermescheck/scanners/observability.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:langsmith|langfuse|opentelemetry|arize|phoenix|`
- `callback.*handler|tracer|telemetry|observ|`
- `cost.*track|token.*count|latency.*track|`
- `span.*create|trace.*start|metric.*record|`
- `promptlayer|helicone|braintrust|smith\.ai|`
- `langsmith\.run|langfuse\.track|otel\.|open telemetry)`
- `: `

## Os Architecture

**Scanner file**: `hermescheck/scanners/os_architecture.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:harness|orchestrator|scheduler|kernel|agent loop|react loop|main loop)\b`
- `\b(?:context|memory|summary|compact|compression|rag|vector|embedding|history)\b`
- `\b(?:page table|page fault|paging|swap(?: in| out)?|lru|hot data|cold data|heat score|ttl|recency|pin(?:ned)?)\b`
- `\b(?:tool use|tool call|tool_call|function calling|function_call|execute[_ -]?shell(?:_command)?|shell command|subprocess|system call|syscall)\b`
- `\b(?:syscall table|capability|capabilities|cap_[a-z0-9_]+|permission matrix|seccomp)\b`
- `: re.compile(
        r`
- `\b(?:time slice|timeslice|deadline|budget|priority|preempt|context switch|yield|cancel|cancellation|backpressure)\b`
- `\b(?:knowledge|skills?|rag|vector[_ -]?store|vectordb|embedding|docs?|notes?|github|resources?)\b`
- `\b(?:vfs|virtual file|mount|mount point|resource path|semantic fs)\b`
- `: `
- `: `
- `) >= 5 and signals.count(`
- `: `
- `,
                `
- `, `
- `: `

## Output Pipeline

**Scanner file**: `hermescheck/scanners/output_pipeline.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:mutate.*response|rewrite.*output|transform.*answer|shape.*response|`
- `post.?process.*llm|stream.*chunk|yield.*token|format.*response|`
- `response.*filter|output.*sanitize|strip.*tag|clean.*response|`
- `response.*hook|after.*llm|post.*llm)`
- `(?:buffer|assemble|reconstruct|join|concat|merge.*stream|`
- `chunk.*buffer|response.*build|output.*assemble|token.*stream)`
- `: `

## Path Filters

**Scanner file**: `hermescheck/scanners/path_filters.py`

**Default severity**: `medium`

**Regex patterns**:

- `,
}

HASHED_BUNDLE_RE = re.compile(
    r`
- `-[a-z0-9_-]{6,}(?:-[a-z0-9_-]{4,})*(?: \d+)?\.(?:js|cjs|mjs)$`
- `^[a-z0-9_.-]+-[a-z0-9_-]{8,}(?: \d+)?\.(?:js|cjs|mjs|css|map)$`
- `.*\.min\.(?:js|cjs|mjs)$`

## Role Play Orchestration

**Scanner file**: `hermescheck/scanners/role_play_orchestration.py`

**Default severity**: `medium`

**Regex patterns**:

- `: re.compile(
        r`
- `: re.compile(r`
- `: re.compile(
        r`
- `: re.compile(
        r`
- `: re.compile(r`
- `(?:\b\w+\s+agent\b|\bagent\s+(?:role|team|crew|department)\b|(?:智能体|代理)\s*(?:角色|团队|部门))`
- `(?:agent|subagent|multi[_ -]?agent|swarm|crew|tool\s+role|handoff|pipeline|chain|智能体|代理|多智能体|交接|接棒|流水线)`
- `(?:handoff|hand[-_ ]?off|pass(?:es|ed)?\s+to|relay|pipeline|chain|next\s+agent|transfer\s+to|`
- `接棒|交接|移交|传给|下一个\s*(?:agent|智能体|代理)|流水线|串行|部门)`
- `(?:tool|script|command|function|workflow|工具|脚本|命令|函数|流程).{0,32}(?:agent|智能体|代理)`
- `: `

## Runtime Complexity

**Scanner file**: `hermescheck/scanners/runtime_complexity.py`

**Default severity**: `medium`

**Regex patterns**:

- `\b(fastapi|flask|express|django|router|api router)\b`
- `\b(streamlit|react|next|vue|svelte|electron|pywebview|tauri)\b`
- `\b(celery|rq|bullmq|rabbitmq|kafka|worker queue)\b`
- `\b(docker|kubernetes|pm2|supervisor|launchd|systemd|nginx|gunicorn)\b`
- `\b(redis|postgres|mysql|mongodb|sqlite|vector store|milvus|pinecone)\b`
- `\b(langchain|autogen|crewai|mcp|swarm|agent loop|tool calling)\b`
- `: `

## Secrets

**Scanner file**: `hermescheck/scanners/secrets.py`

**Default severity**: `critical`

**Regex patterns**:

- `sk-[a-zA-Z0-9]{20,}`
- `ghp_[a-zA-Z0-9]{36}`
- `glpat-[a-zA-Z0-9]{20,}`
- `AKIA[0-9A-Z]{16}`
- `(?i)(?:api[_-]?key|apikey|secret[_-]?key|token)\s*[=:]\s*['\`
- `(?:example|your_|placeholder|xxx|test)`
- `(?:`
- `sk-(?:123|abc|test|fake|dummy|example|x{4,})[a-z0-9_-]*|`
- `dapi(?:123|abc|test|fake|dummy|example)[a-z0-9_-]*|`
- `akia(?:0{8,}|1{8,}|6{8,}|test|fake|dummy|example)[a-z0-9_-]*|`
- `gAAAAABinvalid[a-z0-9_-]*|`
- `(?:1234567890|abcdef){2,}`
- `)`
- `(?:algolia|docsearch|search).*api[_-]?key|api[_-]?key.*(?:algolia|docsearch|search)|`
- `(?:next_public|vite_|public_|publishable)`
- `: `

## Skill Duplication

**Scanner file**: `hermescheck/scanners/skill_duplication.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:skill|sop|runbook|playbook|guide|checklist|instruction)`
- `(?:^|[-_ ])(?:old|new|latest|final|draft|copy|backup|bak|v\d+)(?:$|[-_ ])`
- `[^a-z0-9]+`
- `: `

## Startup Complexity

**Scanner file**: `hermescheck/scanners/startup_complexity.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:launch|start|run|serve|bootstrap|entrypoint|daemon|supervisord|pm2|launchd|docker-compose|compose|procfile|app)\b`
- `(?:subprocess\.run|subprocess\.Popen|os\.system|exec\s+|python\s+-m|node\s+|bash\s+|sh\s+|launchctl|pm2|supervisor)`
- `: `

## Tool Enforcement

**Scanner file**: `hermescheck/scanners/tool_enforcement.py`

**Default severity**: `high`

**Regex patterns**:

- `(?:must use tool|required call|always use|tool is required|`
- `required to call|you must call|mandatory tool use)`
- `(?:tool_call|toolCall|tool_use|function_call|tool_choice|use_tool)`
- `(?:assert |if not |raise |\.validate|\.check|verify|guard|enforce|sanity_check)`
- `: `
- `: `
