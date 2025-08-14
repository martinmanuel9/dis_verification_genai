import streamlit as st
import requests
from utils import *
from components.agent_creator import create_agent_form

FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")

def AI_Agent():
    st.header("Agent Management")
    
    # Agent management sub-modes
    agent_mode = st.radio(
        "Select Action:",
        ["Create New Agent", "Manage Existing Agents"],
        horizontal=True
    )
    
    # ----------------------------------------------------------------------
    # CREATE NEW AGENT SUB-MODE
    # ----------------------------------------------------------------------
    if agent_mode == "Create New Agent":
        # Use the unified agent creation component
        create_agent_form(
            template_category="general",
            key_prefix="ai_agent",
            form_title="Create a New AI Agent"
        )
    # ----------------------------------------------------------------------
    # MANAGE EXISTING AGENTS SUB-MODE
    # ----------------------------------------------------------------------
    elif agent_mode == "Manage Existing Agents":
        st.subheader("Manage Existing Agents")
        
        # Load agents with enhanced error handling
        col1_load, col2_load = st.columns([1, 2])
        
        with col1_load:
            if st.button("Refresh Agent List", key="manage_refresh"):
                try:
                    with st.spinner("Loading agents from database..."):
                        agents_response = requests.get(f"{FASTAPI_API}/get-agents", timeout=10)
                        if agents_response.status_code == 200:
                            agent_data = agents_response.json()
                            st.session_state.agents_data = agent_data.get("agents", [])
                            st.success(f"Loaded {len(st.session_state.agents_data)} agents")
                        else:
                            st.warning(f"Could not load agents (Status: {agents_response.status_code})")
                except Exception as e:
                    st.error(f"Error loading agents: {e}")
        
        with col2_load:
            if st.session_state.agents_data:
                total_agents = len(st.session_state.agents_data)
                active_agents = sum(1 for agent in st.session_state.agents_data if agent.get("is_active", True))
                st.metric("Total Agents", total_agents, delta=f"{active_agents} active")

        # Enhanced agents display
        if st.session_state.agents_data:
            # Create enhanced table data
            agents_data = []
            for agent in st.session_state.agents_data:
                agents_data.append({
                    "ID": agent.get("id", "N/A"),
                    "Name": agent.get("name", "Unknown"),
                    "Model": agent.get("model_name", "Unknown"),
                    "Queries": agent.get("total_queries", 0),
                    "Status": "Active" if agent.get("is_active", True) else "Inactive",
                    "Created": agent.get("created_at", "Unknown")[:10] if agent.get("created_at") else "Unknown",
                    "System Prompt": agent.get("system_prompt", "")[:100] + ("..." if len(agent.get("system_prompt", "")) > 100 else ""),
                    "User Template": agent.get("user_prompt_template", "")[:100] + ("..." if len(agent.get("user_prompt_template", "")) > 100 else "")
                })
            
            # Display in a nice table
            st.dataframe(agents_data, use_container_width=True, height=400)
            
            # Word Export Section
            st.subheader("Export Agents")
            col_export1, col_export2 = st.columns([1, 1])
            
            with col_export1:
                export_format = st.selectbox(
                    "Export Format:",
                    ["detailed", "summary"],
                    help="Detailed includes full prompts and performance metrics"
                )
            
            with col_export2:
                if st.button("Export to Word", type="primary"):
                    try:
                        with st.spinner("Generating Word document..."):
                            # Call FastAPI export endpoint
                            export_response = requests.post(
                                f"{FASTAPI_API}/export-agents-word",
                                params={"export_format": export_format},
                                timeout=30
                            )
                            
                            if export_response.status_code == 200:
                                # Get the base64 content
                                response_data = export_response.json()
                                file_content = response_data.get("content_b64")
                                filename = response_data.get("filename", "agents_export.docx")
                                
                                if file_content:
                                    import base64
                                    doc_bytes = base64.b64decode(file_content)
                                    
                                    st.download_button(
                                        label=f"Download {filename}",
                                        data=doc_bytes,
                                        file_name=filename,
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
                                    st.success("Word document generated successfully!")
                                else:
                                    st.error("No file content received")
                            else:
                                st.error(f"Export failed: {export_response.text}")
                    except Exception as e:
                        st.error(f"Error exporting agents: {str(e)}")
            
            # Management actions
            management_action = st.radio(
                "Management Action:",
                ["View Details", "Edit Agent", "Delete Agent"],
                horizontal=True,
                key="mgmt_action"
            )
            
            # Agent selection for all actions
            agent_options = [f"{agent['name']} (ID: {agent['id']})" for agent in st.session_state.agents_data]
            selected_agent_str = st.selectbox(
                "Select Agent:",
                ["--Select Agent--"] + agent_options,
                key="selected_agent_mgmt"
            )
            
            if selected_agent_str != "--Select Agent--":
                agent_id = int(selected_agent_str.split("ID: ")[1].rstrip(")"))
                selected_agent = next((agent for agent in st.session_state.agents_data if agent["id"] == agent_id), None)
                
                if selected_agent:
                    # VIEW DETAILS
                    if management_action == "View Details":
                        st.subheader(f"Agent Details: {selected_agent['name']}")
                        
                        col1_details, col2_details = st.columns(2)
                        
                        with col1_details:
                            st.markdown("**Basic Information:**")
                            st.json({
                                "ID": selected_agent.get("id"),
                                "Name": selected_agent.get("name"),
                                "Model": selected_agent.get("model_name"),
                                "Created": selected_agent.get("created_at"),
                                "Updated": selected_agent.get("updated_at"),
                                "Status": "Active" if selected_agent.get("is_active", True) else "Inactive"
                            })
                            
                            st.markdown("**Performance Metrics:**")
                            st.json({
                                "Total Queries": selected_agent.get("total_queries", 0),
                                "Temperature": selected_agent.get("temperature", 0.7),
                                "Max Tokens": selected_agent.get("max_tokens", 300)
                            })
                        
                        with col2_details:
                            st.markdown("**System Prompt:**")
                            st.text_area(
                                "Full System Prompt", 
                                selected_agent.get("system_prompt", ""), 
                                height=200, 
                                disabled=True,
                                key="view_system_prompt"
                            )
                            
                            st.markdown("**User Prompt Template:**")
                            st.text_area(
                                "Full User Prompt Template", 
                                selected_agent.get("user_prompt_template", ""), 
                                height=150, 
                                disabled=True,
                                key="view_user_prompt"
                            )
                    
                    # EDIT AGENT
                    elif management_action == "Edit Agent":
                        st.subheader(f"Edit Agent: {selected_agent['name']}")
                        
                        with st.form(f"edit_agent_{agent_id}"):
                            col1_edit, col2_edit = st.columns(2)
                            
                            with col1_edit:
                                new_name = st.text_input(
                                    "Agent Name", 
                                    value=selected_agent.get("name", ""),
                                    key="edit_name"
                                )
                                
                                # Model selection for edit
                                available_models = get_available_models_cached()
                                current_model = selected_agent.get("model_name", "")
                                
                                if current_model in available_models:
                                    model_index = available_models.index(current_model)
                                else:
                                    model_index = 0
                                
                                new_model = st.selectbox(
                                    "Model", 
                                    available_models, 
                                    index=model_index,
                                    key="edit_model"
                                )
                                
                                # Advanced settings
                                new_temperature = st.slider(
                                    "Temperature",
                                    min_value=0.0,
                                    max_value=1.0,
                                    value=selected_agent.get("temperature", 0.7),
                                    step=0.1,
                                    key="edit_temperature"
                                )
                                
                                new_max_tokens = st.number_input(
                                    "Max Tokens",
                                    min_value=100,
                                    max_value=4000,
                                    value=selected_agent.get("max_tokens", 300),
                                    step=100,
                                    key="edit_max_tokens"
                                )
                                
                                new_is_active = st.checkbox(
                                    "Active", 
                                    value=selected_agent.get("is_active", True),
                                    key="edit_active"
                                )
                            
                            with col2_edit:
                                new_system_prompt = st.text_area(
                                    "System Prompt",
                                    value=selected_agent.get("system_prompt", ""),
                                    height=200,
                                    key="edit_system_prompt"
                                )
                                
                                new_user_prompt = st.text_area(
                                    "User Prompt Template",
                                    value=selected_agent.get("user_prompt_template", ""),
                                    height=150,
                                    key="edit_user_prompt"
                                )
                            
                            # Form submission
                            submitted = st.form_submit_button("💾 Update Agent", type="primary")
                            
                            if submitted:
                                # Validation
                                if not new_name or len(new_name.strip()) < 3:
                                    st.error("Agent name must be at least 3 characters")
                                elif "{data_sample}" not in new_user_prompt:
                                    st.error("User prompt template must contain {data_sample} placeholder")
                                else:
                                    # Prepare update payload
                                    update_payload = {
                                        "name": new_name.strip(),
                                        "model_name": new_model,
                                        "system_prompt": new_system_prompt.strip(),
                                        "user_prompt_template": new_user_prompt.strip(),
                                        "temperature": new_temperature,
                                        "max_tokens": new_max_tokens,
                                        "is_active": new_is_active
                                    }
                                    
                                    try:
                                        with st.spinner("Updating agent..."):
                                            response = requests.put(
                                                f"{FASTAPI_API}/update-agent/{agent_id}",
                                                json=update_payload,
                                                timeout=30
                                            )
                                            
                                            if response.status_code == 200:
                                                st.success(f"Agent '{new_name}' updated successfully!")
                                                st.session_state.agents_data = []  # Force refresh
                                                st.rerun()
                                            else:
                                                error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                                                st.error(f"Failed to update agent: {error_detail}")
                                    
                                    except Exception as e:
                                        st.error(f"Error updating agent: {str(e)}")
                    
                    # DELETE AGENT
                    elif management_action == "Delete Agent":
                        st.subheader(f"Delete Agent: {selected_agent['name']}")
                        
                        st.warning("**Permanent Action**: Agent deletion cannot be undone and will remove all associated data.")
                        
                        # Show agent info before deletion
                        with st.expander("Agent to be deleted", expanded=True):
                            st.json({
                                "ID": selected_agent.get("id"),
                                "Name": selected_agent.get("name"),
                                "Model": selected_agent.get("model_name"),
                                "Total Queries": selected_agent.get("total_queries", 0),
                                "Created": selected_agent.get("created_at")
                            })
                        
                        # Confirmation steps
                        confirm_name = st.text_input(
                            f"Type the agent name '{selected_agent['name']}' to confirm deletion:",
                            key="delete_confirm_name"
                        )
                        
                        confirm_delete = st.checkbox(
                            f"I understand this will permanently delete agent: {selected_agent['name']}",
                            key="delete_confirm_checkbox"
                        )
                        
                        if confirm_name == selected_agent['name'] and confirm_delete:
                            if st.button("Confirm Deletion", type="secondary", key="delete_confirm_button"):
                                try:
                                    with st.spinner("Deleting agent..."):
                                        response = requests.delete(f"{FASTAPI_API}/delete-agent/{agent_id}", timeout=10)
                                        
                                        if response.status_code == 200:
                                            st.success("Agent deleted successfully!")
                                            # Force refresh of agents list
                                            st.session_state.agents_data = []
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to delete agent: HTTP {response.status_code}")
                                            
                                except Exception as e:
                                    st.error(f"Error deleting agent: {e}")
                        else:
                            if confirm_name != selected_agent['name'] and confirm_name:
                                st.error("Agent name doesn't match")
                            if not confirm_delete:
                                st.info("Please check the confirmation box and enter the exact agent name to enable deletion")

        else:
            # Enhanced empty state
            st.info("No agents found. Create your first agent in the 'Create New Agent' tab!")
            
            # Quick start guide
            with st.expander("Quick Start Guide"):
                st.markdown("""
                **Getting Started with Agents:**
                
                1. **Switch to 'Create New Agent'** tab above
                2. **Choose a Template**: Select from predefined templates like 'Systems Engineer' or 'Quality Control Engineer'
                3. **Configure Settings**: Adjust temperature (creativity) and max tokens (response length)
                4. **Test Configuration**: Use the test button to preview how your agent will work
                5. **Create Agent**: Click 'Create Agent' to add it to your AI toolkit
                6. **Come back here to manage**: Edit, view details, or delete agents
                """)

    # Enhanced tips and best practices (shown for both modes)
    with st.expander("Agent Best Practices & Tips", expanded=False):
        col1_tips, col2_tips = st.columns(2)
        
        with col1_tips:
            st.markdown("""
            **System Prompt Best Practices:**
            - Define specific expertise areas clearly
            - Include analysis frameworks and methodologies
            - Specify output format and structure
            - Add relevant standards or regulations
            - Use bullet points for clarity
            - Include examples of what to focus on
            """)
            
            st.markdown("""
            **Management Tips:**
            - Regularly review agent performance metrics
            - Update prompts based on usage patterns
            - Deactivate unused agents to keep interface clean
            - Test agents after making changes
            """)
            
        with col2_tips:
            st.markdown("""
            **User Prompt Template Tips:**
            - Always include `{data_sample}` placeholder
            - Provide clear instructions for analysis type
            - Specify desired output structure
            - Include relevant context or constraints
            - Ask for specific recommendations
            - Consider different input types (contracts, policies, etc.)
            """)
            
            st.markdown("""
            **Performance Optimization:**
            - Lower temperature (0.1-0.3) for consistent compliance checks
            - Higher temperature (0.7-0.9) for creative brainstorming
            - Adjust max tokens based on typical response needs
            - Monitor success rates and response times
            """)
        
        st.markdown("""
        **Model Selection Guidelines:**
        - **GPT-4**: Fast local processing, good for privacy-sensitive content
        
        **Temperature Settings:**
        - **0.1-0.3**: Highly consistent, factual analysis (recommended for compliance)
        - **0.4-0.7**: Balanced creativity and consistency (good for general work)
        - **0.8-1.0**: More creative responses (useful for brainstorming or alternative approaches)
        """)