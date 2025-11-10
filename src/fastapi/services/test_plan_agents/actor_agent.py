"""
Actor Agent Implementation

Extracts testable requirements, rules, and specifications from document sections.
Based on the existing _run_single_actor logic from multi_agent_test_plan_service.
"""

from typing import Any, Dict
import logging

from core.agent_base import BaseTestPlanAgent, AgentContext

logger = logging.getLogger(__name__)


class ActorAgent(BaseTestPlanAgent):
    """
    Actor Agent for extracting testable requirements.

    This agent analyzes document sections and extracts:
    - Testable rules and specifications
    - Dependencies between requirements
    - Potential conflicts
    - Measurable acceptance criteria
    """

    def get_system_prompt(self, context: AgentContext) -> str:
        """
        Get system prompt for Actor Agent.

        Args:
            context: Execution context

        Returns:
            System prompt string
        """
        return """You are a compliance and test planning expert specializing in military and technical standards.

Your role is to meticulously analyze technical specifications and extract testable requirements with exceptional detail and precision."""

    def get_user_prompt(self, context: AgentContext) -> str:
        """
        Get user prompt for Actor Agent.

        Args:
            context: Execution context

        Returns:
            User prompt string
        """
        return f"""Analyze the following section of a military standard and extract EVERY possible testable rule, specification, constraint, or requirement.

REQUIREMENTS:
1. Rules MUST be extremely detailed, explicit, and step-by-step
2. Include measurable criteria, acceptable ranges, and referenced figures or tables if mentioned
3. For ambiguous or implicit requirements, describe a specific test strategy
4. Generate a short, content-based TITLE for this section (do not use page numbers)

CRITICAL: ABSOLUTELY DO NOT REPEAT, DUPLICATE, OR PARAPHRASE THE SAME RULE OR LINE. Each requirement, dependency, and test step must appear ONCE ONLY.

OUTPUT FORMAT:
Organize your output using markdown headings and bolded text:

## [Section Title]
**Dependencies:**
- List detailed dependencies as explicit tests, if any.

**Conflicts:**
- List detected or possible conflicts and provide recommendations or mitigation steps.

**Test Rules:**
1. (Very detailed, step-by-step numbered test rules)
2. (Include measurable criteria and acceptance thresholds)
3. (Reference specific figures, tables, or equations if applicable)

---

Section Name: {context.section_title}

Section Text:
{context.section_content}

---

If you find truly nothing testable, reply: 'No testable rules in this section.'
"""

    def parse_response(self, response: str, context: AgentContext) -> Dict[str, Any]:
        """
        Parse Actor Agent response into structured data.

        Args:
            response: Raw LLM response
            context: Execution context

        Returns:
            Dictionary with parsed data
        """
        # Extract section title
        section_title = self._extract_section_title(response)

        # Extract dependencies
        dependencies = self._extract_dependencies(response)

        # Extract conflicts
        conflicts = self._extract_conflicts(response)

        # Extract test rules
        test_rules = self._extract_test_rules(response)

        return {
            'section_title': section_title or context.section_title,
            'rules_extracted': response,
            'dependencies': dependencies,
            'conflicts': conflicts,
            'test_rules': test_rules,
            'has_testable_content': 'no testable rules' not in response.lower()
        }

    def _extract_section_title(self, response: str) -> str:
        """Extract section title from response"""
        import re
        match = re.search(r'^##\s+(.+?)$', response, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _extract_dependencies(self, response: str) -> list:
        """Extract dependencies from response"""
        import re
        deps = []
        deps_section = re.search(
            r'\*\*Dependencies:\*\*\s*(.*?)(?=\*\*|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if deps_section:
            lines = deps_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and line.startswith('-'):
                    deps.append(line[1:].strip())
        return deps

    def _extract_conflicts(self, response: str) -> list:
        """Extract conflicts from response"""
        import re
        conflicts = []
        conflicts_section = re.search(
            r'\*\*Conflicts:\*\*\s*(.*?)(?=\*\*|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if conflicts_section:
            lines = conflicts_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and line.startswith('-'):
                    conflicts.append(line[1:].strip())
        return conflicts

    def _extract_test_rules(self, response: str) -> list:
        """Extract numbered test rules from response"""
        import re
        rules = []
        rules_section = re.search(
            r'\*\*Test Rules:\*\*\s*(.*?)(?=---|\Z)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if rules_section:
            lines = rules_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and re.match(r'^\d+\.', line):
                    rules.append(line)
        return rules
