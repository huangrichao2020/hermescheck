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

## Bug Inference

**Scanner file**: `hermescheck/scanners/bug_inference.py`

**Default severity**: `high`

**Regex patterns**:

- `^(?:fix|patch|repair|hotfix|tmp|temp)\d*\.py$`
- `\b(?:content\.replace|\.replace\s*\(|write_text\s*\(|open\s*\([^)]*['\`
- `renameSync|copyFileSync)\b`
- `['\`
- `\bimport\s*\(\s*([^)]{1,180})\)`
- `\b(?:pathToFileURL|fileURLToPath|import\.meta\.resolve)\b`
- `(?:path|file|filename|entry|script|bundle|resolved|absolute|join|resolve)`
- `\bsetTimeout\s*\(`
- `\bsetTimeout\s*\(.*,\s*[0-9_]+(?:\s*[),;])`
- `(?:delay|timeout|interval|ttl|duration|ms|seconds|minutes|nextRun|wait)`
- `\b(?:Math\.min|Math\.max|clamp|MAX_TIMEOUT|MAX_DELAY|setTimeout cap|timerDelay|safeDelay)\b`
- `(?:heartbeat|cron|schedul|deadline|until|nextRun|expire|expiry|refreshAt|-\s*now|hours?|days?)`
- `(?:debounce|animation|transition|tooltip|scroll|render|search)`
- `: `
- `[A-Z0-9_]+`
- `(?:PATH|FILE|ENTRY|SCRIPT|BUNDLE)`
- `: `
- `: `

## Capability Policy

**Scanner file**: `hermescheck/scanners/capability_policy.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:agent|assistant|tool_call|tool use|function_call|planner|scheduler|autonomous|daemon|`
- `always[-_ ]?on|human[-_ ]?in[-_ ]?the[-_ ]?loop)\b`
- `(?:subprocess\.(?:run|Popen)|os\.system|shell\s*=\s*True|\bexec\s*\(|\beval\s*\(|`
- `write_text\(|write_bytes\(|\.unlink\(|os\.remove\(|shutil\.rmtree\(|`
- `requests\.(?:get|post|put|delete)|httpx\.(?:get|post|put|delete)|\bfetch\s*\(|axios\.`
- `|git\s+push|npm\s+publish|pip\s+install|docker\s+|kubectl\s+|browser_control|playwright|selenium)`
- `\b(?:blocklist|denylist|blacklist|forbidden|blocked_commands|dangerous_commands)\b`
- `\b(?:allowlist|whitelist|auto[-_ ]?approved|safe_commands|allowed_commands|allowed_paths|permitted_paths)\b`
- `\b(?:needs[_ -]?approval|require[_ -]?approval|request[_ -]?approval|confirm|consent|human[_ -]?approval|`
- `ask[_ -]?to[_ -]?continue|manual_review)\b`
- `\b(?:read[_ -]?scope|write[_ -]?scope|path[_ -]?scope|temp[_ -]?scope|workspace[_ -]?scope|`
- `permission matrix|capability table|capabilities|sandbox)\b`
- `\b(?:def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|`
- `async\s+def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|`
- `(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)\s*\(|`
- `tool_call\s*\(|function_call\s*\(|subprocess\.(?:run|Popen)|os\.system\s*\()\b`
- `\b(?:check[_ -]?permission|PermissionEngine|permission_engine|is_allowed|is_blocked|deny|denied|`
- `require[_ -]?approval|needs[_ -]?approval|allowed_commands|blocked_commands|blocklist|allowlist|`
- `capability[_ -]?check|policy\.check)\b`
- `: `
- `: `

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

## Daemon Lifecycle

**Scanner file**: `hermescheck/scanners/daemon_lifecycle.py`

**Default severity**: `medium`

**Regex patterns**:

- `\b(?:daemon|gateway|watchdog|run_forever|always[-_ ]?on|service|systemd|launchagent|pm2|supervisor|`
- `detached|pid[_ -]?file|background worker|heartbeat)\b`
- `\b(?:restart|reload|replace|respawn|crash|backoff|SIGTERM|SIGKILL|kill\s+-|terminate)\b`
- `\b(?:active[_ -]?(?:agents|runs|jobs|tasks|sessions)|running[_ -]?(?:jobs|tasks|sessions)|`
- `job[_ -]?queue|task[_ -]?queue|inflight|in[-_ ]?flight|pending[_ -]?jobs|session[_ -]?state)\b`
- `\b(?:drain|graceful[_ -]?(?:shutdown|restart|stop)|quiesce|wait[_ -]?for[_ -]?(?:idle|jobs)|`
- `stop[_ -]?accepting|pre[_ -]?restart|restart[_ -]?barrier|safe[_ -]?restart)\b`
- `\b(?:checkpoint|resume|recover|replay|journal|side[-_ ]?effect[_ -]?log|operation[_ -]?log|`
- `idempotent|session[_ -]?replay|state[_ -]?restore|crash[_ -]?recovery)\b`
- `\b(?:connected|health[_ -]?check|status|ready|readiness|websocket|gateway[_ -]?state|post[_ -]?restart)\b`
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

## Loop Safety

**Scanner file**: `hermescheck/scanners/loop_safety.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:agent[_ -]?loop|main[_ -]?loop|react[_ -]?loop|tool[_ -]?loop|while\s+True|for\s*\(\s*;;|`
- `while\s*\(\s*true\s*\)|loop_detector|run_forever|always[-_ ]?on|daemon)\b`
- `\b(?:tool_call|toolCall|tool_use|function_call|execute[_ -]?shell|shell command|subprocess|`
- `delegate_task|retry|fallback|provider fallback)\b`
- `\b(?:cron|scheduler|heartbeat|interval|setInterval|schedule\.|task[_ -]?queue|job[_ -]?queue|`
- `worker[_ -]?queue|workerQueue|background[_ -]?task|backgroundTask|daemon|watchdog)\b`
- `\b(?:max[_ -]?(?:steps|turns|iterations|loops|retries)|iteration[_ -]?limit|tool[_ -]?call[_ -]?limit|`
- `loop[_ -]?detector|repetition[_ -]?detector|same[_ -]?args|args[_ -]?hash|dedupe|circuit[_ -]?breaker|`
- `timeout|deadline|retry[_ -]?budget|backoff|ask[_ -]?to[_ -]?continue|confirm[_ -]?continue|`
- `cancel|cancellation|abort|stop[_ -]?signal)\b`
- `\b(?:def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|`
- `async\s+def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|`
- `(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)\s*\(|`
- `tool_call\s*\(|function_call\s*\(|subprocess\.(?:run|Popen)|os\.system\s*\()\b`
- `\b(?:loop[_ -]?detector|repetition[_ -]?detector|record[_ -]?tool|record\s*\(|same[_ -]?args|`
- `args[_ -]?hash|max[_ -]?(?:steps|turns|iterations|loops|retries)|retry[_ -]?budget|timeout|deadline|`
- `circuit[_ -]?breaker|ask[_ -]?to[_ -]?continue)\b`
- `: [],
        `
- `].append(f`
- `: `
- `: `
- `] and refs[`
- `: `
- `, `

## Memory Freshness

**Scanner file**: `hermescheck/scanners/memory_freshness.py`

**Default severity**: `medium`

**Regex patterns**:

- `(?:memory|checkpoint|archive|summary|history|session|state|snapshot|insight)`
- `(?:^|[-_ ])(?:old|new|latest|final|draft|copy|backup|bak|v\d+)(?:$|[-_ ])`
- `[^a-z0-9]+`
- `: `

## Memory Lifecycle

**Scanner file**: `hermescheck/scanners/memory_lifecycle.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:memory|memories|remember|recall|profile|preference|facts?|episode|reflection|vector store|`
- `embedding|sqlite|fts5|semantic search|second brain|history|summary)\b|(?:记忆|回忆|偏好|事实|反思)`
- `\b(?:identity|preference|goal|project|habit|decision|constraint|relationship|episode|reflection|`
- `memory[_ -]?type|fact[_ -]?type)\b`
- `\b(?:top[_ -]?k|limit|char(?:acter)?[_ -]?limit|token[_ -]?budget|context[_ -]?budget|retrieval[_ -]?budget|`
- `max[_ -]?(?:tokens|chars|memories)|fts5|full[-_ ]?text search)\b`
- `\b(?:confidence|conflict|contradiction|merge|dedupe|duplicate|overlap|similarity|newer wins|`
- `resolve[_ -]?conflict|coalesce|canonical)\b`
- `\b(?:active|durable|ttl|decay|retention|reinforce|reinforcement|prune|dismiss|dismissed|stale|`
- `expire|expiration|aging|archive)\b`
- `\b(?:pointer|anchor|source_ref|evidence_ref|semantic_hash|topic_anchor|page fault|page table|swap in)\b`
- `)}
    files = list(iter_source_files(target))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        try:
            lines = fp.read_text(encoding=`
- `].append(ref)
    return refs


def _evidence(refs: dict[str, list[str]], *keys: str, limit: int = 9) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for key in keys:
        for ref in refs.get(key, []):
            if ref not in seen:
                out.append(ref)
                seen.add(ref)
            if len(out) >= limit:
                return out
    return out


def scan_memory_lifecycle(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    if len(refs[`
- `],
    }
    present = {name: values for name, values in governance.items() if values}
    if len(present) >= 3:
        return []

    governance_summary = `
- `: `
- `),
            `

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

## Memory Retrieval I18N

**Scanner file**: `hermescheck/scanners/memory_retrieval_i18n.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:fts5|full[-_ ]?text search|MATCH|unicode61|sqlite[_ -]?fts|[A-Za-z0-9_]+_fts)\b`
- `\bunicode61\b`
- `\b(?:cjk|chinese|japanese|korean|multilingual|i18n|unicode|locale|non[-_ ]?english)\b|`
- `(?:中文|汉字|漢字|日文|韩文|韓文|多语言|多語言)`
- `\b(?:ngram|bi[-_ ]?gram|tri[-_ ]?gram|jieba|janome|mecab|kuromoji|sentencepiece|`
- `custom[_ -]?tokenizer|tokenize_for_fts|fts_match_query|like[_ -]?fallback|fallback[_ -]?like|`
- `embedding[_ -]?fallback|semantic[_ -]?fallback|vector[_ -]?fallback|reindex|rebuild[_ -]?index)\b`
- `(?:中文回复|后端|用户偏好|多语言|cjk|unicode61|ngram|trigram|fts.*中文|中文.*fts|`
- `japanese|korean|non[-_ ]?english)`
- `: `
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
- `\b(?:context replay|conversation replay|transcript replay|session replay|chat history|`
- `stored conversation|conversation history|runstate|run state|previous_response_id|conversation id)\b|`
- `(?:上下文回放|录像带|聊天记录|会话历史|读档)`
- `\b(?:environment state|environment is the state|filesystem state|file system state|workspace state|`
- `working tree|server state|durable filesystem|durable workspace|persistent workspace|on-disk state)\b|`
- `(?:环境即状态|环境状态|现场|服务器文件|硬盘|物理生效)`
- `\b(?:side[-_ ]?effect log|action log|operation log|audit log|journal|write[-_ ]?ahead|`
- `commit log|trajectory|tool result|command output|execution record)\b|`
- `(?:副作用记录|动作日志|操作日志|执行记录|工具结果|命令输出)`
- `\b(?:idempotent recovery|idempotent resume|retry[-_ ]?safe|resumable run|resume after interruption|`
- `interrupted run|wake[-_ ]?up instruction|system interrupt|recovery checkpoint|durable execution)\b|`
- `(?:幂等恢复|幂等续接|自动续接|唤醒指令|中断恢复|恢复检查点)`
- `: re.compile(
        r`
- `qwen|codex|claude|gemini|opencode)\b.{0,80}\b(?:cli|command|subprocess|worker|spawn|process|pool)\b|`
- `\b(?:subprocess\.run|subprocess\.Popen|create_subprocess_exec)\b.{0,120}\b(?:qwen|codex|claude|gemini|opencode)\b|`
- `(?:外部\s*LLM|代码\s*CLI|CLI\s*进程池|命令行\s*worker|拉起\s*qwen|拉起\s*codex|拉起\s*claude)`
- `\b(?:task json|task file|task envelope|work order|handoff file|job spec|delegation spec|`
- `structured task|task manifest)\b|(?:任务\s*JSON|任务文件|任务信封|工作单|交接文件|结构化任务)`
- `\b(?:natural language prompt|natural-language prompt|prompt text|worker prompt|stdin prompt|`
- `to_prompt|task file path|read this task file|do not send raw json|not raw json|no raw json)\b|`
- `(?:自然语言\s*Prompt|自然语言提示|worker\s*提示词|stdin\s*提示词|不要裸(?:扔|传)\s*JSON|不能裸(?:扔|传)\s*JSON)`
- `\b(?:stdout|stderr|exit code|returncode|capture_output|completedprocess|standard output|`
- `process output|worker result)\b|(?:标准输出|标准错误|退出码|返回码|捕获输出|worker\s*结果)`
- `\b(?:process pool|worker pool|timeout|deadline|concurrency|semaphore|queue|cancel|cancellation|`
- `asyncio\.create_subprocess_exec|subprocess\.run\(.{0,80}timeout)\b|(?:进程池|worker\s*池|超时|并发|取消|队列)`
- `: `
- `: `
- `) >= 5 and signals.count(`
- `: `
- `,
                `
- `, `
- `: `
- `: `
- `) >= 2 and (
        signals.count(`
- `: `
- `,
                    `

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

## Pipeline Middleware Integrity

**Scanner file**: `hermescheck/scanners/pipeline_middleware_integrity.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:pipeline|pipelines|middleware|filter|filters|inbound|outbound|pre[_ -]?process|post[_ -]?process|`
- `before[_ -]?(?:llm|model)|after[_ -]?(?:llm|model)|request[_ -]?filter|response[_ -]?filter)\b`
- `\b(?:sanitize|redact|mask|moderation|translate|rewrite|inject[_ -]?prompt|transform[_ -]?(?:message|response)|`
- `strip|replace|content[_ -]?filter|pii|sensitive)\b`
- `\b(?:priority|order|sequence|sort|chain|before|after|stage|rank|position)\b`
- `\b(?:raw[_ -]?(?:message|response|request)|transformed[_ -]?(?:message|response|request)|audit[_ -]?log|`
- `trace|span|diff|before[_ -]?after|log[_ -]?mutation|original[_ -]?content)\b`
- `\b(?:fail[_ -]?(?:open|closed)|on[_ -]?error|try\s*:|except|catch|fallback|skip[_ -]?filter|`
- `filter[_ -]?error|raise|timeout)\b`
- `, `
- `].append(ref)
            if AUDIT_RE.search(line):
                refs[`
- `: `
- `]:
        findings.append(
            {
                `
- `: `
- `),
                `
- `: `

## Plugin Execution Policy

**Scanner file**: `hermescheck/scanners/plugin_execution_policy.py`

**Default severity**: `critical`

**Regex patterns**:

- `\b(?:plugin|plugins|function|functions|pipe|valves|user[_ -]?valves|extension|extensions|`
- `load[_ -]?plugin|plugin[_ -]?loader|dynamic[_ -]?tool|custom[_ -]?tool)\b`
- `\b(?:exec\s*\(|eval\s*\(|compile\s*\(|importlib|__import__|load_module|module_from_spec|`
- `exec_module|dynamic[_ -]?import)\b`
- `\b(?:pip\s+install|uv\s+pip\s+install|subprocess\.(?:run|Popen).*pip|requirements|dependencies|`
- `install[_ -]?requirements|frontmatter)\b`
- `\b(?:sandbox|allowlist|denylist|blocklist|permission|capability|scope|isolat(?:e|ion)|`
- `container|venv|virtualenv|timeout|resource[_ -]?limit|read[_ -]?scope|write[_ -]?scope)\b`
- `\b(?:hash|sha256|pinned|pin|lockfile|allowlisted[_ -]?packages|allowed[_ -]?packages|`
- `package[_ -]?allowlist|constraints\.txt|requirements\.lock)\b`
- `\b(?:admin[_ -]?only|user[_ -]?plugin|tenant|owner|role|rbac|oauth|auth|trusted|untrusted|`
- `review|approval|enable[_ -]?plugin|disable[_ -]?plugin)\b`
- `: `
- `: `

## Rag Pipeline Governance

**Scanner file**: `hermescheck/scanners/rag_pipeline_governance.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:rag|retrieval[_ -]?augmented|knowledge[_ -]?base|vector[_ -]?(?:store|db|search)|`
- `embedding|embeddings|document[_ -]?(?:loader|upload|ingest)|chroma|qdrant|milvus|faiss|`
- `bm25|hybrid[_ -]?search|rerank|reranker)\b`
- `\b(?:chunk[_ -]?(?:size|overlap)|text[_ -]?splitter|recursivecharactertextsplitter|split[_ -]?documents|`
- `token[_ -]?splitter|document[_ -]?chunk)\b`
- `\b(?:top[_ -]?k|limit|score[_ -]?threshold|max[_ -]?(?:tokens|chars|context|documents)|`
- `context[_ -]?budget|retrieval[_ -]?budget|similarity[_ -]?threshold|rerank[_ -]?top[_ -]?k)\b`
- `\b(?:full[_ -]?context|rag[_ -]?full[_ -]?context|bypass[_ -]?embedding|bypass[_ -]?retrieval|`
- `skip[_ -]?retrieval|raw[_ -]?document|entire[_ -]?document)\b`
- `\b(?:ingest[_ -]?status|embedding[_ -]?status|async[_ -]?embedding|retry|backoff|dedupe|`
- `content[_ -]?hash|document[_ -]?(?:id|version)|index[_ -]?version|reindex|failed[_ -]?documents)\b`
- `: `
- `: `

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

## Self Evolution Capability

**Scanner file**: `hermescheck/scanners/self_evolution_capability.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:agent|agent[_ -]?loop|orchestrator|subagent|tool[_ -]?call|function[_ -]?call|memory|`
- `scheduler|rag|mcp|plugin|skill|llm)\b|(?:智能体|工具调用|记忆|技能)`
- `\b(?:external[_ -]?signal|signal[_ -]?(?:intake|screening)|upstream|reference[_ -]?project|`
- `competitor|benchmark|issue|pull request|pr|release note|production log|user feedback|github trend)\b|`
- `(?:外部信号|信号筛选|热门项目|用户反馈|线上日志|上游项目)`
- `\b(?:source[_ -]?reading|read[_ -]?source|code archaeology|architecture review|directory tree|`
- `entrypoint|main loop|core class|adr|design doc|decision record|boundary analysis)\b|`
- `(?:解剖学习|读源码|目录结构|主入口|核心类|设计决策|边界分析)`
- `\b(?:pattern[_ -]?extraction|extract(?:ed)? pattern|design pattern|reusable pattern|generalize|`
- `generalization|not copy|not copied|not a code copy|anti[_ -]?copy)\b|`
- `(?:提取模式|设计模式|举一反三|不是照搬|不照搬|不是代码副本)`
- `\b(?:constraint[_ -]?adapt(?:ation)?|fit constraints|local constraints|zero heavy dependencies|`
- `no heavy dependenc(?:y|ies)|lightweight|2gb ram|bounded resource|integrate with existing)\b|`
- `(?:约束适配|本地约束|零重型依赖|轻量|2GB|融入已有)`
- `\b(?:small[_ -]?step|minimal implementation|independent module|isolated module|try/except|`
- `fail[_ -]?soft|non[_ -]?intrusive|feature flag|rollback|bounded change)\b|`
- `(?:小步落地|最小实现|独立模块|不侵入|可回滚|失败不影响)`
- `\b(?:verification[_ -]?loop|validation loop|eval|regression test|smoke test|acceptance|`
- `self[_ -]?test|test passed|post[_ -]?change review|retro|lesson learned)\b|`
- `(?:验证闭环|回归测试|烟测|验收|复盘|教训)`
- `: `
- `: `
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

## Token Usage

**Scanner file**: `hermescheck/scanners/token_usage.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:agent|agent loop|orchestrator|subagent|tool_call|llm|chat|model)\b|智能体`
- `\b(?:max[_ -]?context[_ -]?tokens|max[_ -]?(?:context|tokens)|context[_ -]?(?:window|length|tokens|limit)|`
- `token[_ -]?(?:budget|limit)|input[_ -]?tokens)\b`
- `(?<![\w.])([0-9][0-9_,.]*)\s*([kKmM万]?)(?:\s*(?:tokens?|context))?`
- `\b(?:full[_ -]?(?:history|context|transcript)|all[_ -]?(?:messages|history|memory|context)|`
- `entire[_ -]?(?:history|conversation|repo|repository|workspace|context)|conversation[_ -]?history|`
- `session[_ -]?history|chat[_ -]?history|transcript|load[_ -]?all|read[_ -]?all|include[_ -]?all)\b`
- `\b(?:rglob\s*\(\s*['\`
- `readFileSync\s*\(|readFile\s*\(|load_all_files|read_repository|scan_workspace)\b`
- `\b(?:prompt|messages|context|system[_ -]?prompt|chat|completion|llm|model|createChatCompletion|responses\.create)\b`
- `\b(?:token[_ -]?budget|max[_ -]?(?:tokens|chars|messages|context)|char(?:acter)?[_ -]?limit|`
- `truncate|trim|prune|top[_ -]?k|retrieval[_ -]?budget|summary|summarize|compact|compression|`
- `page[_ -]?table|paging|lru|cache|content[_ -]?hash|skill|sop|workflow|layered[_ -]?memory|`
- `right knowledge|relevant knowledge|less noise)\b|(?:分层记忆|省\s*token|极致省\s*Token|技能|经验固化)`
- `(?:<\s*30k|不到\s*30k|30k context|fraction of the 200k|200k.?1m|layered memory|`
- `\bL[0-4]\b|crystalliz(?:e|es|ing)|skill tree|direct recall|right knowledge|less noise|`
- `minimal toolset|9 atomic tools|~100[- ]line agent loop|token efficient|极致省\s*Token|分层记忆|`
- `固化为\s*Skill|下次同类任务直接调用|关键信息始终在场)`
- `: `
- `: `
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

## Tool Server Boundary

**Scanner file**: `hermescheck/scanners/tool_server_boundary.py`

**Default severity**: `high`

**Regex patterns**:

- `\b(?:mcp|model[_ -]?context[_ -]?protocol|openapi|swagger|tool[_ -]?server|remote[_ -]?tool|`
- `external[_ -]?tool|tool[_ -]?server[_ -]?connections|openapi\.json|/mcp)\b`
- `\b(?:openapi\.json|swagger\.json|requests\.(?:get|post)|httpx\.(?:get|post)|fetch\s*\(|axios\.|`
- `load[_ -]?spec|tool[_ -]?manifest|server[_ -]?url|base[_ -]?url)\b`
- `\b(?:allowlist|denylist|blocklist|trusted[_ -]?servers|allowed[_ -]?(?:servers|tools|hosts)|`
- `permission|capability|approval|scope|auth|oauth|api[_ -]?key|bearer|timeout|retry[_ -]?budget|`
- `rate[_ -]?limit|schema[_ -]?validation|jsonschema)\b`
- `\b(?:sha256|hash|fingerprint|pinned[_ -]?(?:spec|schema|version)|version[_ -]?pin|etag|`
- `schema[_ -]?version|lockfile)\b`
- `\b(?:write[_ -]?file|delete[_ -]?file|shell|terminal|subprocess|exec|browser|playwright|selenium|`
- `git\s+push|npm\s+publish|docker|kubectl|database|sql|filesystem|network)\b`
- `: `
- `: `
- `: `
