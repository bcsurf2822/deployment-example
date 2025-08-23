Subagents are specialized AI assistants that operate in separate context windows with focused expertise. They enable Claude to delegate specific tasks to experts, improving quality and efficiency.

### Understanding Subagents

Each subagent:
- Has its own context window (no pollution from main conversation)
- Operates with specialized system prompts
- Can be limited to specific tools
- Works autonomously on delegated tasks

### Example Subagents in This Repository

**Documentation Manager** (`.claude/agents/documentation-manager.md`):
- Automatically updates docs when code changes
- Ensures README accuracy
- Maintains API documentation
- Creates migration guides

**Validation Gates** (`.claude/agents/validation-gates.md`):
- Runs all tests after changes
- Iterates on fixes until tests pass
- Enforces code quality standards
- Never marks tasks complete with failing tests

### Creating Your Own Subagents

1. Use the `/agents` command or create a file in `.claude/agents/`:

```markdown
---
name: security-auditor
description: "Security specialist. Proactively reviews code for vulnerabilities and suggests improvements."
tools: Read, Grep, Glob
---

You are a security auditing specialist focused on identifying and preventing security vulnerabilities...

## Core Responsibilities
1. Review code for OWASP Top 10 vulnerabilities
2. Check for exposed secrets or credentials
3. Validate input sanitization
4. Ensure proper authentication/authorization
...
```

### Subagent Best Practices

**1. Focused Expertise**: Each subagent should have one clear specialty

**2. Proactive Descriptions**: Use "proactively" in descriptions for automatic invocation:
```yaml
description: "Code reviewer. Proactively reviews all code changes for quality."
```

**3. Tool Limitations**: Only give subagents the tools they need:
```yaml
tools: Read, Grep  # No write access for review-only agents
```

**4. Information Flow Design**: Understand how information flows from primary agent → subagent → primary agent. The subagent description is crucial because it tells your primary Claude Code agent when and how to use it. Include clear instructions in the description for how the primary agent should prompt this subagent.

**5. One-Shot Context**: Subagents don't have full conversation history - they receive a single prompt from your primary agent. Design your subagents with this limitation in mind.

Learn more in the [Subagents documentation](https://docs.anthropic.com/en/docs/claude-code/sub-agents).

*Note: While other AI assistants don't have formal subagents, you can achieve similar results by creating specialized prompts and switching between different conversation contexts.*

---