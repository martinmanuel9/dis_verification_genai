"""
Critic Agent Implementation

Synthesizes and deduplicates outputs from multiple Actor agents.
Creates a single, cohesive set of test procedures from multiple perspectives.
"""

from typing import Any, Dict, List
import logging
import re

from core.agent_base import BaseTestPlanAgent, AgentContext

logger = logging.getLogger(__name__)


class CriticAgent(BaseTestPlanAgent):
    """
    Critic Agent for synthesizing actor outputs.

    This agent reviews outputs from multiple Actor agents and:
    - Synthesizes a single, cohesive set of requirements
    - Eliminates redundancies and duplicates
    - Corrects errors and inconsistencies
    - Ensures comprehensive coverage
    """

    def get_system_prompt(self, context: AgentContext) -> str:
        """
        Get system prompt for Critic Agent.

        Args:
            context: Execution context

        Returns:
            System prompt string
        """
        return """You are a senior test planning reviewer with expertise in synthesizing multiple perspectives into cohesive test plans.

Your role is to critically analyze multiple requirement extractions and create a single, authoritative test plan that:
- Captures all unique requirements
- Eliminates redundancies
- Corrects errors or misinterpretations
- Ensures logical organization and completeness"""

    def get_user_prompt(self, context: AgentContext) -> str:
        """
        Get user prompt for Critic Agent.

        Args:
            context: Execution context with actor_results in previous_results

        Returns:
            User prompt string
        """
        # Get actor results from context
        actor_results = context.previous_results.get('actor_results', [])

        if not actor_results:
            return "ERROR: No actor results provided for criticism"

        # Prepare actor outputs
        actor_outputs_text = ""
        for i, result in enumerate(actor_results, 1):
            model_name = result.get('model_name', 'unknown')
            agent_id = result.get('agent_id', 'unknown')
            rules = result.get('rules_extracted', '')
            actor_outputs_text += f"\n\n### Actor {i}: Model {model_name} ({agent_id})\n{rules}\n{'='*40}"

        return f"""You are a senior test planning reviewer (Critic AI).

Given the following section and rules extracted by several different AI models, do the following:

1. Carefully review and compare the provided rule sets
2. Synthesize a SINGLE, detailed and explicit set of testable rules
3. Eliminate redundancies, correct errors, and ensure all requirements are present
4. Ensure the final test plan is step-by-step, detailed, and well organized

CRITICAL INSTRUCTIONS:
- NEVER simply combine all lines verbatim—synthesize, deduplicate, and streamline
- If a rule, step, or line has the same or similar meaning as another, KEEP ONLY ONE
- Preserve the most detailed and accurate version of each unique requirement
- Identify and resolve any contradictions between actor outputs

OUTPUT FORMAT:
Present your result in markdown format with these headings:

## [Section Title]
**Dependencies:**
- List detailed dependencies as explicit tests, if any

**Conflicts:**
- List detected or possible conflicts and provide recommendations

**Test Rules:**
1. (Synthesized, deduplicated test rules)
2. (Ensure each rule appears only once)

---

Section Name: {context.section_title}

Section Text:
{context.section_content}

---

Actor Outputs from {len(actor_results)} AI models:
{actor_outputs_text}

---

Synthesize these outputs into a single, authoritative test plan."""

    def parse_response(self, response: str, context: AgentContext) -> Dict[str, Any]:
        """
        Parse Critic Agent response into structured data.

        Args:
            response: Raw LLM response
            context: Execution context

        Returns:
            Dictionary with parsed data
        """
        # Apply deduplication
        deduplicated_response = self._deduplicate_markdown(response)

        # Extract structured data
        dependencies = self._extract_dependencies(deduplicated_response)
        conflicts = self._extract_conflicts(deduplicated_response)
        test_procedures = self._extract_test_procedures(deduplicated_response)
        test_rules = self._extract_test_rules(deduplicated_response)

        actor_results = context.previous_results.get('actor_results', [])

        return {
            'section_title': context.section_title,
            'synthesized_rules': deduplicated_response,
            'dependencies': dependencies,
            'conflicts': conflicts,
            'test_procedures': test_procedures,
            'test_rules': test_rules,
            'actor_count': len(actor_results)
        }

    def _deduplicate_markdown(self, text: str) -> str:
        """
        Remove duplicate lines from markdown text.

        Args:
            text: Markdown text

        Returns:
            Deduplicated text
        """
        lines = text.split('\n')
        seen = set()
        deduplicated_lines = []

        for line in lines:
            # Normalize line for comparison (lowercase, strip whitespace)
            normalized = line.strip().lower()

            # Skip empty lines or keep headers
            if not normalized or line.strip().startswith('#'):
                deduplicated_lines.append(line)
                continue

            # Check for duplicates
            if normalized not in seen:
                seen.add(normalized)
                deduplicated_lines.append(line)

        return '\n'.join(deduplicated_lines)

    def _extract_dependencies(self, response: str) -> List[str]:
        """Extract dependencies from response"""
        deps = []
        deps_section = re.search(
            r'\*\*Dependencies:\*\*\s*(.*?)(?=\*\*|##|$)',
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

    def _extract_conflicts(self, response: str) -> List[str]:
        """Extract conflicts from response"""
        conflicts = []
        conflicts_section = re.search(
            r'\*\*Conflicts:\*\*\s*(.*?)(?=\*\*|##|$)',
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

    def _extract_test_procedures(self, response: str) -> List[Dict[str, Any]]:
        """Extract test procedures as structured data"""
        procedures = []
        rules = self._extract_test_rules(response)

        for idx, rule in enumerate(rules, 1):
            procedures.append({
                'test_id': f"TEST-{idx:03d}",
                'description': rule,
                'dependencies': [],
                'conflicts': []
            })

        return procedures

    def _extract_test_rules(self, response: str) -> List[str]:
        """Extract numbered test rules from response"""
        rules = []
        rules_section = re.search(
            r'\*\*Test Rules:\*\*\s*(.*?)(?=---|\*\*|##|\Z)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if rules_section:
            lines = rules_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and re.match(r'^\d+\.', line):
                    # Remove the number prefix
                    rule_text = re.sub(r'^\d+\.\s*', '', line)
                    if rule_text:
                        rules.append(rule_text)
        return rules
