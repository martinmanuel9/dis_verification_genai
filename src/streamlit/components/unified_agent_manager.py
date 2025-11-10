"""
Unified Agent Manager Component

Single component for managing ALL agents and agent sets in the system.
All agents and agent sets are database-backed.

Supports:
- Individual Agents: Actor, Critic, Contradiction Detection, Gap Analysis, Custom
- Agent Sets: Orchestration pipelines combining multiple agents
- Full CRUD operations for both agents and agent sets
"""

import streamlit as st
from config.settings import config
from lib.api.client import api_client
import json
from datetime import datetime
from typing import Optional, Dict, List
from collections import Counter

# API endpoints - unified database-backed system
TEST_PLAN_AGENT_API = f"{config.fastapi_url}/api/test-plan-agents"
AGENT_SET_API = f"{config.fastapi_url}/api/agent-sets"


def render_unified_agent_manager():
    """
    Main entry point for Unified Agent Manager.
    Manages both individual agents and agent sets (orchestration pipelines).
    """
    st.title("Agent & Orchestration Manager")
    st.markdown("""
    Unified interface for managing AI agents and orchestration pipelines.

    **Agents**: Individual AI agents with specific roles (Actor, Critic, QA, etc.)
    **Agent Sets**: Orchestration pipelines that combine multiple agents in stages
    """)

    # Top-level navigation: Agents vs Agent Sets
    main_tab1, main_tab2 = st.tabs(["Individual Agents", "Agent Sets (Pipelines)"])

    with main_tab1:
        # Sub-tabs for agent management
        agent_tab1, agent_tab2, agent_tab3, agent_tab4 = st.tabs([
            "View Agents",
            "Create Agent",
            "Manage Agents",
            "Help & Info"
        ])

        with agent_tab1:
            render_agent_list_view()

        with agent_tab2:
            render_create_agent_form()

        with agent_tab3:
            render_manage_agents_view()

        with agent_tab4:
            render_help_info()

    with main_tab2:
        # Sub-tabs for agent set management
        set_tab1, set_tab2, set_tab3 = st.tabs([
            "View Agent Sets",
            "Create Agent Set",
            "Analytics"
        ])

        with set_tab1:
            render_view_agent_sets()

        with set_tab2:
            render_create_agent_set()

        with set_tab3:
            render_agent_set_analytics()


def fetch_agents_cached(agent_type_filter: str = "All", include_inactive: bool = False, force_refresh: bool = False):
    """
    Fetch agents with session state caching for better UX.

    Args:
        agent_type_filter: Filter by agent type or "All"
        include_inactive: Include inactive agents
        force_refresh: Force refresh from API

    Returns:
        Tuple of (agents list, total_count)
    """
    # Create cache key based on filters
    cache_key = f"agents_{agent_type_filter}_{include_inactive}"

    # Check if we need to fetch (first time or forced refresh)
    if force_refresh or cache_key not in st.session_state:
        params = {"include_inactive": include_inactive}
        if agent_type_filter != "All":
            params["agent_type"] = agent_type_filter

        try:
            response = api_client.get(TEST_PLAN_AGENT_API, params=params)
            if response and "agents" in response:
                agents = response["agents"]
                total_count = response.get("total_count", len(agents))

                # Cache the results
                st.session_state[cache_key] = {
                    "agents": agents,
                    "total_count": total_count,
                    "timestamp": datetime.now()
                }
                return agents, total_count
            else:
                return [], 0
        except Exception as e:
            st.error(f"Error loading agents: {str(e)}")
            return [], 0
    else:
        # Return cached results
        cached = st.session_state[cache_key]
        return cached["agents"], cached["total_count"]


def render_agent_list_view():
    """
    Display list of agents with filtering options and auto-load.
    """
    st.subheader("Agent List")

    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        agent_type_filter = st.selectbox(
            "Filter by Agent Type",
            ["All", "actor", "critic", "contradiction", "gap_analysis", "general", "rule_development"],
            key="agent_type_filter",
            help="Filter agents by their type"
        )

    with col2:
        include_inactive = st.checkbox("Include Inactive", value=False, key="include_inactive")

    with col3:
        force_refresh = st.button("Refresh", use_container_width=True)

    # Fetch agents (cached on first load, refreshed on button click)
    try:
        with st.spinner("Loading agents..." if force_refresh else None):
            agents, total_count = fetch_agents_cached(
                agent_type_filter,
                include_inactive,
                force_refresh=force_refresh
            )

        if agents:
            st.success(f"Found {total_count} agent(s)")

            # Display agents grouped by type
            agent_types = {}
            for agent in agents:
                agent_type = agent["agent_type"]
                if agent_type not in agent_types:
                    agent_types[agent_type] = []
                agent_types[agent_type].append(agent)

            # Render each agent type group
            for agent_type, type_agents in agent_types.items():
                with st.expander(f"**{agent_type.upper()}** ({len(type_agents)} agents)", expanded=True):
                    for agent in type_agents:
                        render_agent_card(agent)
        else:
            st.info("No agents found. Create one using the 'Create Agent' tab.")

    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")


def render_agent_card(agent: Dict):
    """
    Render a single agent card with details and quick actions.
    """
    # Status badge
    status_color = "[ACTIVE]" if agent["is_active"] else "[INACTIVE]"
    default_badge = "System Default" if agent["is_system_default"] else "Custom"

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"### {status_color} {agent['name']}")
        st.markdown(f"*{default_badge}* | Model: **{agent['model_name']}**")

    with col2:
        st.markdown(f"**ID:** {agent['id']}")
        st.markdown(f"**Active:** {'Yes' if agent['is_active'] else 'No'}")

    # Details in columns
    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        st.markdown(f"**Temperature:** {agent['temperature']}")
        st.markdown(f"**Max Tokens:** {agent['max_tokens']}")

        if agent.get('description'):
            st.markdown(f"**Description:** {agent['description']}")

    with detail_col2:
        st.markdown(f"**Created:** {agent.get('created_at', 'N/A')[:10]}")
        st.markdown(f"**Updated:** {agent.get('updated_at', 'N/A')[:10]}")
        if agent.get('created_by'):
            st.markdown(f"**Created By:** {agent['created_by']}")

    # Expandable prompts
    with st.expander("View Prompts"):
        st.text_area("System Prompt", agent['system_prompt'], height=150, disabled=True, key=f"sys_{agent['id']}")
        st.text_area("User Prompt Template", agent['user_prompt_template'], height=150, disabled=True, key=f"usr_{agent['id']}")

    st.markdown("---")


def render_create_agent_form():
    """
    Form to create a new agent.
    """
    st.subheader("Create a New Agent")

    # Agent type selection
    agent_type = st.selectbox(
        "Agent Type",
        ["actor", "critic", "contradiction", "gap_analysis", "general", "rule_development"],
        help="Select the type of agent to create"
    )

    # Show type-specific info
    type_info = {
        "actor": "Extracts testable requirements from document sections with detailed analysis",
        "critic": "Synthesizes and deduplicates outputs from multiple actor agents",
        "contradiction": "Detects contradictions and conflicts in test procedures",
        "gap_analysis": "Identifies missing requirements and test coverage gaps",
        "general": "General purpose agent for systems/quality/test engineering",
        "rule_development": "Specialized in document analysis and test plan creation"
    }
    st.info(f"**{agent_type.upper()}**: {type_info.get(agent_type, '')}")

    with st.form("create_agent_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Agent Name *", placeholder="e.g., 'Custom Actor Agent'")
            model_name = st.selectbox(
                "LLM Model *",
                config.get_available_models(),
                help="Select the language model to use"
            )
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1,
                                   help="Lower = more focused, Higher = more creative")
            max_tokens = st.number_input("Max Tokens", 100, 32000, 4000, 100,
                                        help="Maximum response length")

        with col2:
            description = st.text_area("Description", height=100,
                                      placeholder="Brief description of this agent's purpose")
            is_active = st.checkbox("Active", value=True, help="Whether this agent is active")
            created_by = st.text_input("Created By", placeholder="Your name (optional)")

        system_prompt = st.text_area(
            "System Prompt *",
            height=200,
            placeholder="Define the agent's role, expertise, and behavior...",
            help="Core instructions that define the agent's personality and capabilities"
        )

        user_prompt_template = st.text_area(
            "User Prompt Template *",
            height=200,
            placeholder="Template for user interactions. Use placeholders like {section_title}, {section_content}, etc.",
            help="Template that will be filled with actual data during execution"
        )

        # Advanced settings
        with st.expander("Advanced Settings (Optional)"):
            metadata_json = st.text_area(
                "Metadata (JSON)",
                value="{}",
                help="Additional configuration as JSON"
            )

        # Submit button
        submitted = st.form_submit_button("Create Agent", type="primary", use_container_width=True)

        if submitted:
            # Validation
            if not name or len(name.strip()) < 3:
                st.error("Agent name must be at least 3 characters")
            elif not system_prompt or len(system_prompt.strip()) < 10:
                st.error("System prompt must be at least 10 characters")
            elif not user_prompt_template or len(user_prompt_template.strip()) < 10:
                st.error("User prompt template must be at least 10 characters")
            else:
                # Parse metadata
                try:
                    metadata = json.loads(metadata_json) if metadata_json.strip() else {}
                except json.JSONDecodeError:
                    st.error("Invalid JSON in metadata field")
                    return

                # Prepare payload
                payload = {
                    "name": name.strip(),
                    "agent_type": agent_type,
                    "model_name": model_name,
                    "system_prompt": system_prompt.strip(),
                    "user_prompt_template": user_prompt_template.strip(),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "is_active": is_active,
                    "is_system_default": False,
                    "description": description.strip() if description else None,
                    "created_by": created_by.strip() if created_by else None,
                    "metadata": metadata
                }

                try:
                    with st.spinner("Creating agent..."):
                        response = api_client.post(TEST_PLAN_AGENT_API, data=payload)

                        if response:
                            st.success(f"Agent '{name}' created successfully!")
                            # Clear cache to force refresh
                            for key in list(st.session_state.keys()):
                                if key.startswith("agents_"):
                                    del st.session_state[key]
                            st.balloons()
                        else:
                            st.error("Failed to create agent")
                except Exception as e:
                    st.error(f"Error creating agent: {str(e)}")


def render_manage_agents_view():
    """
    Manage existing agents (edit, delete, clone, activate/deactivate).
    """
    st.subheader("Manage Existing Agents")

    # Fetch all agents
    agents, _ = fetch_agents_cached("All", include_inactive=True, force_refresh=False)

    if not agents:
        st.info("No agents found. Create one in the 'Create Agent' tab.")
        return

    # Agent selection
    agent_options = {f"{agent['name']} (ID: {agent['id']})": agent for agent in agents}
    selected_option = st.selectbox(
        "Select Agent to Manage",
        ["--Select Agent--"] + list(agent_options.keys())
    )

    if selected_option == "--Select Agent--":
        return

    agent = agent_options[selected_option]

    # Management actions
    action = st.radio(
        "Action",
        ["View Details", "Edit", "Clone", "Activate/Deactivate", "Delete"],
        horizontal=True
    )

    if action == "View Details":
        render_view_details(agent)
    elif action == "Edit":
        render_edit_agent(agent)
    elif action == "Clone":
        render_clone_agent(agent)
    elif action == "Activate/Deactivate":
        render_toggle_active(agent)
    elif action == "Delete":
        render_delete_agent(agent)


def render_view_details(agent: Dict):
    """View full agent details."""
    st.subheader(f"Agent Details: {agent['name']}")

    col1, col2 = st.columns(2)

    with col1:
        st.json({
            "ID": agent['id'],
            "Name": agent['name'],
            "Type": agent['agent_type'],
            "Model": agent['model_name'],
            "Temperature": agent['temperature'],
            "Max Tokens": agent['max_tokens'],
            "Active": agent['is_active'],
            "System Default": agent['is_system_default']
        })

    with col2:
        st.json({
            "Created": agent.get('created_at'),
            "Updated": agent.get('updated_at'),
            "Created By": agent.get('created_by'),
            "Description": agent.get('description')
        })

    st.text_area("System Prompt", agent['system_prompt'], height=200, disabled=True)
    st.text_area("User Prompt Template", agent['user_prompt_template'], height=200, disabled=True)

    if agent.get('metadata'):
        st.json(agent['metadata'])


def render_edit_agent(agent: Dict):
    """Edit agent form."""
    st.subheader(f"Edit Agent: {agent['name']}")

    with st.form("edit_agent_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_name = st.text_input("Agent Name", value=agent['name'])
            new_model = st.selectbox(
                "Model",
                config.get_available_models(),
                index=config.get_available_models().index(agent['model_name']) if agent['model_name'] in config.get_available_models() else 0
            )
            new_temperature = st.slider("Temperature", 0.0, 1.0, agent['temperature'], 0.1)
            new_max_tokens = st.number_input("Max Tokens", 100, 32000, agent['max_tokens'], 100)

        with col2:
            new_description = st.text_area("Description", value=agent.get('description', ''), height=100)
            new_is_active = st.checkbox("Active", value=agent['is_active'])

        new_system_prompt = st.text_area("System Prompt", value=agent['system_prompt'], height=200)
        new_user_prompt = st.text_area("User Prompt Template", value=agent['user_prompt_template'], height=200)

        submitted = st.form_submit_button("Update Agent", type="primary")

        if submitted:
            payload = {
                "name": new_name,
                "model_name": new_model,
                "system_prompt": new_system_prompt,
                "user_prompt_template": new_user_prompt,
                "temperature": new_temperature,
                "max_tokens": new_max_tokens,
                "is_active": new_is_active,
                "description": new_description if new_description else None
            }

            try:
                with st.spinner("Updating agent..."):
                    api_client.put(f"{TEST_PLAN_AGENT_API}/{agent['id']}", data=payload)
                    st.success("Agent updated successfully!")
                    # Clear cache
                    for key in list(st.session_state.keys()):
                        if key.startswith("agents_"):
                            del st.session_state[key]
                    st.rerun()
            except Exception as e:
                st.error(f"Error updating agent: {str(e)}")


def render_clone_agent(agent: Dict):
    """Clone agent form."""
    st.subheader(f"Clone Agent: {agent['name']}")
    st.info("Create a copy of this agent with a new name")

    with st.form("clone_agent_form"):
        new_name = st.text_input("New Agent Name", placeholder=f"{agent['name']} (Copy)")
        created_by = st.text_input("Created By", placeholder="Your name (optional)")

        submitted = st.form_submit_button("Clone Agent", type="primary")

        if submitted:
            if not new_name or len(new_name.strip()) < 3:
                st.error("New name must be at least 3 characters")
            else:
                payload = {"new_name": new_name.strip(), "created_by": created_by.strip() if created_by else None}
                try:
                    with st.spinner("Cloning agent..."):
                        api_client.post(f"{TEST_PLAN_AGENT_API}/{agent['id']}/clone", data=payload)
                        st.success(f"Agent cloned as '{new_name}'!")
                        for key in list(st.session_state.keys()):
                            if key.startswith("agents_"):
                                del st.session_state[key]
                        st.rerun()
                except Exception as e:
                    st.error(f"Error cloning agent: {str(e)}")


def render_toggle_active(agent: Dict):
    """Toggle agent active status."""
    st.subheader(f"Toggle Active Status: {agent['name']}")

    current_status = "Active" if agent['is_active'] else "Inactive"
    new_status = "Inactive" if agent['is_active'] else "Active"

    st.info(f"Current status: **{current_status}**")
    st.warning(f"This will change the status to: **{new_status}**")

    endpoint = f"{TEST_PLAN_AGENT_API}/{agent['id']}/{'deactivate' if agent['is_active'] else 'activate'}"

    if st.button(f"Confirm: Set to {new_status}", type="primary"):
        try:
            with st.spinner(f"Setting agent to {new_status}..."):
                api_client.post(endpoint)
                st.success(f"Agent is now {new_status}")
                for key in list(st.session_state.keys()):
                    if key.startswith("agents_"):
                        del st.session_state[key]
                st.rerun()
        except Exception as e:
            st.error(f"Error updating status: {str(e)}")


def render_delete_agent(agent: Dict):
    """Delete agent with confirmation."""
    st.subheader(f"Delete Agent: {agent['name']}")

    if agent['is_system_default']:
        st.error("Cannot delete system default agents")
        return

    st.warning("**PERMANENT ACTION**: Deleting an agent cannot be undone.")

    with st.expander("Agent to be deleted", expanded=True):
        st.json({
            "ID": agent['id'],
            "Name": agent['name'],
            "Type": agent['agent_type'],
            "Created": agent.get('created_at')
        })

    confirm_name = st.text_input(f"Type '{agent['name']}' to confirm deletion:")
    confirm_check = st.checkbox("I understand this is permanent")

    if confirm_name == agent['name'] and confirm_check:
        if st.button("Confirm Deletion", type="secondary"):
            try:
                with st.spinner("Deleting agent..."):
                    api_client.delete(f"{TEST_PLAN_AGENT_API}/{agent['id']}")
                    st.success("Agent deleted successfully")
                    for key in list(st.session_state.keys()):
                        if key.startswith("agents_"):
                            del st.session_state[key]
                    st.rerun()
            except Exception as e:
                st.error(f"Error deleting agent: {str(e)}")


def render_help_info():
    """Display help and best practices."""
    st.subheader("Agent Management Guide")

    st.markdown("""
    ## Agent Types

    ### Test Plan Agents
    - **Actor**: Extracts testable requirements from documents
    - **Critic**: Synthesizes multiple actor outputs
    - **Contradiction**: Detects conflicts in test procedures
    - **Gap Analysis**: Identifies missing test coverage

    ### General & Custom Agents
    - **General**: Systems/Quality/Test engineering agents
    - **Rule Development**: Document analysis specialists
    - **Custom**: Create your own specialized agents

    ## Best Practices

    ### System Prompts
    - Define clear expertise areas
    - Include analysis frameworks
    - Specify output formats
    - Reference relevant standards
    - Use bullet points for clarity

    ### User Prompt Templates
    - Use placeholders for dynamic content:
      - `{section_title}`, `{section_content}` for test plan agents
      - `{data_sample}` for general agents
      - Custom placeholders as needed
    - Provide clear instructions
    - Specify desired output structure

    ### Temperature Settings
    - **0.1-0.3**: Consistent, factual (compliance checks)
    - **0.4-0.7**: Balanced (general work)
    - **0.8-1.0**: Creative (brainstorming)

    ### Model Selection
    - **GPT-4**: Recommended for most use cases
    - **Claude**: Alternative for specific tasks
    - Consider cost vs. quality trade-offs

    ## Management Tips
    - Review agent performance regularly
    - Update prompts based on usage
    - Deactivate unused agents
    - Test after making changes
    - Clone before major edits
    """)

# ======================================================================
# AGENT SET MANAGEMENT FUNCTIONS
# ======================================================================

def render_view_agent_sets():
    """View and manage existing agent sets with detailed agent information"""
    st.subheader("Existing Agent Sets")

    # Fetch agent sets
    try:
        response = api_client.get(AGENT_SET_API)
        agent_sets = response.get("agent_sets", [])
    except Exception as e:
        st.error(f"Failed to load agent sets: {e}")
        return

    if not agent_sets:
        st.info("No agent sets found. Create your first agent set using the 'Create Agent Set' tab!")
        return

    # Filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search by name", key="agent_set_search")
    with col2:
        show_inactive = st.checkbox("Show inactive", value=False, key="show_inactive_sets")

    # Filter agent sets
    filtered_sets = agent_sets
    if not show_inactive:
        filtered_sets = [s for s in filtered_sets if s.get('is_active', True)]
    if search_term:
        filtered_sets = [s for s in filtered_sets if search_term.lower() in s.get('name', '').lower()]

    st.write(f"**Total Agent Sets:** {len(filtered_sets)}")

    # Fetch all agents for detailed display
    try:
        agents_response = api_client.get(TEST_PLAN_AGENT_API)
        all_agents = agents_response.get("agents", [])
        agent_map = {a['id']: a for a in all_agents}
    except Exception as e:
        st.warning(f"Could not load agent details: {e}")
        agent_map = {}

    # Display agent sets
    for agent_set in filtered_sets:
        prefix = "[System Default]" if agent_set.get('is_system_default') else "[Custom]"
        with st.expander(f"{prefix} {agent_set['name']}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**Description:** {agent_set.get('description', 'No description')}")
                st.write(f"**Type:** {agent_set.get('set_type', 'sequence')}")
                st.write(f"**Usage Count:** {agent_set.get('usage_count', 0)}")
                st.write(f"**Active:** {'Yes' if agent_set.get('is_active') else 'No'}")
                st.write(f"**System Default:** {'Yes' if agent_set.get('is_system_default') else 'No'}")

                # Show pipeline configuration with detailed agent info
                st.write("**Pipeline Stages:**")
                stages = agent_set.get('set_config', {}).get('stages', [])
                for idx, stage in enumerate(stages, 1):
                    st.markdown(f"**Stage {idx}: {stage.get('stage_name')}**")
                    st.write(f"- Execution Mode: {stage.get('execution_mode')}")
                    if stage.get('description'):
                        st.caption(f"{stage.get('description')}")

                    # Show agent details
                    agent_ids = stage.get('agent_ids', [])
                    if agent_ids:
                        agent_counts = Counter(agent_ids)
                        st.write(f"- Agents ({len(agent_ids)} total):")

                        for agent_id, count in agent_counts.items():
                            agent = agent_map.get(agent_id)
                            if agent:
                                with st.container(border=True):
                                    st.markdown(f"**{agent['name']}** (x{count})")

                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        st.write(f"Type: {agent.get('agent_type', 'N/A')}")
                                        st.write(f"Model: {agent.get('model_name', 'N/A')}")
                                        st.write(f"Temperature: {agent.get('temperature', 0.0)}")
                                    with col_b:
                                        st.write(f"Max Tokens: {agent.get('max_tokens', 'N/A')}")
                                        st.write(f"Active: {'Yes' if agent.get('is_active') else 'No'}")

                                    # Show prompts
                                    with st.expander(f"View Prompts - {agent['name']}"):
                                        st.markdown("**System Prompt:**")
                                        st.code(agent.get('system_prompt', 'No system prompt'), language="text")
                                        st.markdown("**User Prompt Template:**")
                                        st.code(agent.get('user_prompt_template', 'No user prompt template'), language="text")
                            else:
                                st.warning(f"Agent ID {agent_id} not found (x{count})")
                    st.markdown("---")

            with col2:
                st.write("**Actions:**")

                # Clone button
                if st.button("Clone", key=f"clone_{agent_set['id']}"):
                    st.session_state[f'clone_set_{agent_set["id"]}'] = True

                # Edit button (not for system defaults)
                if not agent_set.get('is_system_default'):
                    if st.button("Edit", key=f"edit_{agent_set['id']}"):
                        st.session_state[f'edit_set_{agent_set["id"]}'] = True

                # Activate/Deactivate button
                if agent_set.get('is_active'):
                    if st.button("Deactivate", key=f"deactivate_{agent_set['id']}"):
                        deactivate_agent_set(agent_set['id'])
                else:
                    if st.button("Activate", key=f"activate_{agent_set['id']}"):
                        activate_agent_set(agent_set['id'])

                # Delete button (not for system defaults)
                if not agent_set.get('is_system_default'):
                    if st.button("Delete", key=f"delete_{agent_set['id']}", type="secondary"):
                        if st.session_state.get(f'confirm_delete_{agent_set["id"]}'):
                            delete_agent_set(agent_set['id'])
                        else:
                            st.session_state[f'confirm_delete_{agent_set["id"]}'] = True
                            st.warning("Click again to confirm deletion")

            # Handle clone dialog
            if st.session_state.get(f'clone_set_{agent_set["id"]}'):
                st.write("---")
                new_name = st.text_input(
                    "New name for cloned set:",
                    value=f"{agent_set['name']} (Copy)",
                    key=f"clone_name_{agent_set['id']}"
                )
                if st.button("Confirm Clone", key=f"confirm_clone_{agent_set['id']}"):
                    clone_agent_set(agent_set['id'], new_name)
                    st.session_state.pop(f'clone_set_{agent_set["id"]}')
                    st.rerun()


def render_create_agent_set():
    """Create a new agent set"""
    st.subheader("Create New Agent Set")

    # Fetch available agents (outside form)
    try:
        agents_response = api_client.get(TEST_PLAN_AGENT_API)
        available_agents = agents_response.get("agents", [])
        active_agents = [a for a in available_agents if a.get('is_active', True)]
    except Exception as e:
        st.error(f"Failed to load agents: {e}")
        active_agents = []

    if not active_agents:
        st.error("No active agents available. Please create agents first in the 'Individual Agents' tab.")
        return

    # Initialize stages in session state
    if 'new_set_stages' not in st.session_state:
        st.session_state.new_set_stages = []

    # Stage builder (OUTSIDE FORM - has buttons)
    st.markdown("---")
    st.subheader("Pipeline Stages")
    st.info("Add stages to define your pipeline. Each stage can have multiple agents.")

    # Display current stages
    for idx, stage in enumerate(st.session_state.new_set_stages):
        with st.container(border=True):
            st.write(f"**Stage {idx + 1}: {stage['stage_name']}**")
            st.write(f"- Agents: {len(stage['agent_ids'])} ({stage['execution_mode']})")
            if stage.get('description'):
                st.caption(stage['description'])

    # Add stage section (OUTSIDE FORM)
    with st.expander("Add New Stage", expanded=len(st.session_state.new_set_stages) == 0):
        stage_name = st.text_input(
            "Stage Name",
            placeholder="e.g., actor, critic, qa",
            key="new_stage_name"
        )

        stage_desc = st.text_input(
            "Stage Description (optional)",
            placeholder="e.g., 3 actor agents analyze sections in parallel",
            key="new_stage_desc"
        )

        execution_mode = st.selectbox(
            "Execution Mode",
            options=["parallel", "sequential", "batched"],
            help="parallel: all agents run concurrently, sequential: one after another",
            key="new_stage_mode"
        )

        # Agent selector with counts
        agent_options = {f"{a['name']} (ID: {a['id']})": a['id'] for a in active_agents}
        selected_agent_keys = st.multiselect(
            "Select Agents for this Stage",
            options=list(agent_options.keys()),
            help="You can select the same agent multiple times by selecting it once and specifying count below",
            key="new_stage_agents"
        )

        # Allow duplicating agents
        if selected_agent_keys:
            agent_count = st.number_input(
                "Number of instances for first selected agent",
                min_value=1,
                max_value=10,
                value=1,
                help="Use this to run the same agent multiple times (e.g., 3 actor agents)",
                key="new_stage_count"
            )

        if st.button("Add Stage to Pipeline", key="add_stage_btn"):
            if stage_name and selected_agent_keys:
                # Build agent_ids list (with duplicates if count > 1)
                agent_ids = []
                first_agent_id = agent_options[selected_agent_keys[0]]
                agent_ids.extend([first_agent_id] * int(agent_count))
                # Add other agents once
                for key in selected_agent_keys[1:]:
                    agent_ids.append(agent_options[key])

                new_stage = {
                    "stage_name": stage_name,
                    "agent_ids": agent_ids,
                    "execution_mode": execution_mode,
                    "description": stage_desc if stage_desc else None
                }
                st.session_state.new_set_stages.append(new_stage)
                st.success(f"Added stage: {stage_name}")
                st.rerun()
            else:
                st.error("Please provide stage name and select at least one agent")

    # Clear stages button (OUTSIDE FORM)
    if st.session_state.new_set_stages:
        if st.button("Clear All Stages", key="clear_stages"):
            st.session_state.new_set_stages = []
            st.rerun()

    # Agent set creation form (ONLY basic info and submit)
    st.markdown("---")
    st.subheader("Create Agent Set")
    with st.form("create_agent_set_form"):
        set_name = st.text_input(
            "Set Name *",
            placeholder="e.g., My Custom Pipeline",
            help="Unique name for this agent set"
        )

        description = st.text_area(
            "Description",
            placeholder="Describe the purpose and use case for this agent set...",
            help="Optional description"
        )

        set_type = st.selectbox(
            "Set Type",
            options=["sequence", "parallel", "custom"],
            help="sequence: stages run in order, parallel: all agents run at once"
        )

        # Submit button
        submitted = st.form_submit_button("Create Agent Set", type="primary")

        if submitted:
            if not set_name:
                st.error("Please provide a set name")
            elif not st.session_state.new_set_stages:
                st.error("Please add at least one stage")
            else:
                # Create agent set
                set_config = {
                    "stages": st.session_state.new_set_stages
                }

                payload = {
                    "name": set_name,
                    "description": description,
                    "set_type": set_type,
                    "set_config": set_config,
                    "is_system_default": False,
                    "is_active": True
                }

                try:
                    response = api_client.post(AGENT_SET_API, data=payload)
                    st.success(f"Agent set '{set_name}' created successfully!")
                    st.session_state.new_set_stages = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create agent set: {e}")


def render_agent_set_analytics():
    """Show analytics for agent sets"""
    st.subheader("Agent Set Analytics")

    try:
        # Get most used sets
        response = api_client.get(f"{AGENT_SET_API}/most-used/top?limit=10")
        top_sets = response.get("agent_sets", [])

        if top_sets:
            st.write("**Most Used Agent Sets:**")
            for idx, agent_set in enumerate(top_sets, 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{idx}. **{agent_set['name']}**")
                    st.caption(agent_set.get('description', 'No description'))
                with col2:
                    st.metric("Usage", agent_set.get('usage_count', 0))
        else:
            st.info("No usage data yet. Start generating documents with agent sets!")

    except Exception as e:
        st.error(f"Failed to load analytics: {e}")


# Helper functions for agent set operations
def clone_agent_set(set_id: int, new_name: str):
    """Clone an existing agent set"""
    try:
        response = api_client.post(
            f"{AGENT_SET_API}/{set_id}/clone",
            data={"new_name": new_name}
        )
        st.success(f"Agent set cloned as '{new_name}'")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to clone agent set: {e}")


def delete_agent_set(set_id: int):
    """Delete an agent set"""
    try:
        api_client.delete(f"{AGENT_SET_API}/{set_id}")
        st.success("Agent set deleted successfully")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to delete agent set: {e}")


def activate_agent_set(set_id: int):
    """Activate an agent set"""
    try:
        api_client.put(
            f"{AGENT_SET_API}/{set_id}",
            data={"is_active": True}
        )
        st.success("Agent set activated")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to activate agent set: {e}")


def deactivate_agent_set(set_id: int):
    """Deactivate an agent set"""
    try:
        api_client.put(
            f"{AGENT_SET_API}/{set_id}",
            data={"is_active": False}
        )
        st.success("Agent set deactivated")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to deactivate agent set: {e}")
