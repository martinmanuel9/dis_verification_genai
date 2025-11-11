"""
Document Generator Component
"""
import streamlit as st
import base64
import time
from config.settings import config
from lib.api.client import api_client
from services.chromadb_service import chromadb_service


def Document_Generator():
    st.header("Document Generator")
    # ----------------------------
    # Load pipeline_id from URL first (before anything else)
    # ----------------------------
    if "pipeline_id" in st.query_params:
        url_pipeline_id = st.query_params["pipeline_id"]
        if "pipeline_id" not in st.session_state or st.session_state.pipeline_id != url_pipeline_id:
            st.session_state.pipeline_id = url_pipeline_id

    # ----------------------------
    # Check if there's an active pipeline - if yes, show status only
    # ----------------------------
    if "pipeline_id" in st.session_state and st.session_state.pipeline_id:
        pipeline_id = st.session_state.pipeline_id

        st.info(f"Active Pipeline: `{pipeline_id}`")

        # Show current status
        try:
            status_response = api_client.get(
                f"{config.endpoints.doc_gen}/generation-status/{pipeline_id}",
                timeout=10
            )
            status = status_response.get("status", "unknown")
            progress_msg = status_response.get("progress_message", "")

            # Normalize status to lowercase for comparison
            status_lower = status.lower()

            if status_lower == "completed":
                st.success(f"Generation completed!")

                # Get result
                try:
                    result_response = api_client.get(
                        f"{config.endpoints.doc_gen}/generation-result/{pipeline_id}",
                        timeout=30
                    )
                    docs = result_response.get("documents", [])

                    if docs and len(docs) > 0:
                        primary_doc = docs[0]
                        st.success(f"Document ready: **{primary_doc['title']}**")

                        # Stats
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Sections", primary_doc.get('total_sections', 0))
                        col2.metric("Requirements", primary_doc.get('total_requirements', 0))
                        col3.metric("Test Procedures", primary_doc.get('total_test_procedures', 0))

                        # Download button
                        if 'docx_b64' in primary_doc and primary_doc['docx_b64']:
                            blob = base64.b64decode(primary_doc["docx_b64"])
                            st.download_button(
                                label=f"📥 Download {primary_doc['title']}.docx",
                                data=blob,
                                file_name=f"{primary_doc['title']}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="download_completed_doc",
                                type="primary"
                            )

                        # Clear pipeline to start fresh
                        if st.button("Start New Generation", key="clear_pipeline"):
                            if "pipeline_id" in st.session_state:
                                del st.session_state.pipeline_id
                            if "pipeline_id" in st.query_params:
                                del st.query_params["pipeline_id"]
                            st.rerun()
                    else:
                        st.warning("No documents found in result")
                        if st.button("Clear and Retry", key="clear_failed"):
                            if "pipeline_id" in st.session_state:
                                del st.session_state.pipeline_id
                            if "pipeline_id" in st.query_params:
                                del st.query_params["pipeline_id"]
                            st.rerun()

                except Exception as e:
                    st.error(f"Failed to retrieve result: {e}")
                    if st.button("Clear and Retry", key="clear_error"):
                        if "pipeline_id" in st.session_state:
                            del st.session_state.pipeline_id
                        if "pipeline_id" in st.query_params:
                            del st.query_params["pipeline_id"]
                        st.rerun()

            elif status_lower == "failed":
                st.error(f"Generation failed")
                st.error(f"Error: {status_response.get('error', 'Unknown error')}")

                if st.button("Clear and Retry", key="clear_failed_pipeline"):
                    if "pipeline_id" in st.session_state:
                        del st.session_state.pipeline_id
                    if "pipeline_id" in st.query_params:
                        del st.query_params["pipeline_id"]
                    st.rerun()

            elif status_lower == "cancelling":
                st.warning(f"Generation is being cancelled...")
                st.write(f"**Status:** {status}")
                st.write(f"**Message:** {progress_msg}")
                st.info("The pipeline will stop at the next checkpoint and may return partial results.")

                if st.button("Refresh Status", key="refresh_cancelling"):
                    st.rerun()

                if st.button("Clear Pipeline", key="clear_cancelling"):
                    if "pipeline_id" in st.session_state:
                        del st.session_state.pipeline_id
                    if "pipeline_id" in st.query_params:
                        del st.query_params["pipeline_id"]
                    st.rerun()

            elif status_lower in ["queued", "processing", "initializing"]:
                st.info(f"Generation in progress...")

                # Show detailed progress
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", status.upper())
                with col2:
                    sections_done = status_response.get("sections_processed", "0")
                    total_sections = status_response.get("total_sections", "?")
                    st.metric("Sections", f"{sections_done}/{total_sections}")
                with col3:
                    created_at = status_response.get("created_at", "")
                    if created_at:
                        from datetime import datetime
                        try:
                            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            elapsed = datetime.now() - created.replace(tzinfo=None)
                            minutes = int(elapsed.total_seconds() / 60)
                            st.metric("Elapsed", f"{minutes}m")
                        except:
                            st.metric("Elapsed", "N/A")

                st.write(f"**Progress:** {progress_msg}")

                # Control buttons
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Refresh Status", key="manual_refresh", type="secondary", use_container_width=True):
                        st.rerun()
                with col2:
                    if st.button("Cancel Generation", key="cancel_pipeline", type="primary", use_container_width=True):
                        try:
                            cancel_response = api_client.post(
                                f"{config.endpoints.doc_gen}/cancel-pipeline/{pipeline_id}",
                                data={},
                                timeout=10
                            )
                            st.success("Cancellation requested!")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to cancel: {e}")

                st.markdown("---")

                # Auto-polling option (now enabled by default)
                enable_auto_poll = st.checkbox("Enable auto-refresh (every 10 seconds)", value=True, key="enable_poll")

                if enable_auto_poll:
                    st.caption("Auto-refreshing every 10 seconds...")

                    # Use empty placeholders that can be updated (not appended to)
                    progress_bar_placeholder = st.empty()
                    status_placeholder = st.empty()
                    timestamp_placeholder = st.empty()

                    max_checks = 60  # 10 minutes of polling
                    consecutive_failures = 0

                    for i in range(max_checks):
                        time.sleep(10)

                        try:
                            status_response = api_client.get(
                                f"{config.endpoints.doc_gen}/generation-status/{pipeline_id}",
                                timeout=15
                            )
                            current_status = status_response.get("status", "unknown")
                            progress_msg = status_response.get("progress_message", "")
                            sections_done = status_response.get("sections_processed", "0")
                            total_sections = status_response.get("total_sections", "?")

                            # Calculate progress percentage
                            try:
                                if total_sections != "?" and int(total_sections) > 0:
                                    progress_pct = int(sections_done) / int(total_sections)
                                else:
                                    progress_pct = (i + 1) % 100 / 100
                            except:
                                progress_pct = (i + 1) % 100 / 100

                            # Update placeholders (replaces content, doesn't append)
                            progress_bar_placeholder.progress(progress_pct)
                            status_placeholder.caption(f"{current_status.upper()} | Sections: {sections_done}/{total_sections} | {progress_msg}")
                            timestamp_placeholder.caption(f"Last updated: {time.strftime('%H:%M:%S')}")

                            consecutive_failures = 0

                            if current_status.lower() in ["completed", "failed"]:
                                st.success(f"Status changed to: {current_status}")
                                time.sleep(2)
                                st.rerun()
                                break

                        except Exception as e:
                            consecutive_failures += 1
                            status_placeholder.caption(f"Connection issue (attempt {consecutive_failures}/3): Server is busy processing...")

                            if consecutive_failures >= 3:
                                st.warning("Auto-refresh stopped due to connection issues. Click 'Refresh Status' button to check manually.")
                                break

                            time.sleep(15)

            else:
                st.warning(f"Unknown status: {status}")
                if st.button("Clear Pipeline", key="clear_unknown"):
                    if "pipeline_id" in st.session_state:
                        del st.session_state.pipeline_id
                    if "pipeline_id" in st.query_params:
                        del st.query_params["pipeline_id"]
                    st.rerun()

        except Exception as e:
            st.error(f"Failed to check status: {e}")
            if st.button("Clear Pipeline and Retry", key="clear_status_error"):
                if "pipeline_id" in st.session_state:
                    del st.session_state.pipeline_id
                if "pipeline_id" in st.query_params:
                    del st.query_params["pipeline_id"]
                st.rerun()

        # Stop here - don't show form fields when pipeline is active
        st.stop()

    # ----------------------------
    # No active pipeline - show form fields
    # ----------------------------
    st.subheader("Agent Orchestration")

    # Fetch available agent sets
    try:
        agent_sets_response = api_client.get(f"{config.fastapi_url}/api/agent-sets")
        agent_sets = agent_sets_response.get("agent_sets", [])
        active_agent_sets = [s for s in agent_sets if s.get('is_active', True)]
    except Exception as e:
        st.warning(f"Could not load agent sets: {e}")
        active_agent_sets = []

    # Agent set selector
    if active_agent_sets:
        agent_set_options = [s['name'] for s in active_agent_sets]
        selected_agent_set = st.selectbox(
            "Select Agent Pipeline",
            options=agent_set_options,
            key="gen_agent_set",
            help="Choose an agent set to define the orchestration pipeline."
        )

        # Show agent set details
        agent_set = next((s for s in active_agent_sets if s['name'] == selected_agent_set), None)
        if agent_set:
            with st.expander("View Agent Set Configuration"):
                st.write(f"**Description:** {agent_set.get('description', 'No description')}")
                st.write(f"**Type:** {agent_set.get('set_type', 'sequence')}")
                st.write(f"**Usage Count:** {agent_set.get('usage_count', 0)}")
                st.write("**Pipeline Stages:**")
                for idx, stage in enumerate(agent_set.get('set_config', {}).get('stages', []), 1):
                    st.write(f"  {idx}. **{stage.get('stage_name')}** - {len(stage.get('agent_ids', []))} agent(s) ({stage.get('execution_mode')})")
                    if stage.get('description'):
                        st.caption(f"     {stage.get('description')}")
    else:
        st.error("No agent sets available. Please create an agent set in the Agent Set Manager.")
        st.stop()

    # ----------------------------
    # 2) Select source documents
    # ----------------------------
    st.markdown("---")
    st.subheader("Source Documents")

    if "collections" not in st.session_state:
        st.session_state.collections = chromadb_service.get_collections()

    collections = st.session_state.collections

    if not collections:
        st.warning("No collections available. Please upload documents first.")
        st.stop()

    # Pick collection & load source docs
    source_collection = st.selectbox(
        "Select Collection",
        collections,
        key="gen_source_coll",
    )

    if st.button("Load Source Documents", key="gen_load_sources"):
        with st.spinner("Loading source documents..."):
            try:
                documents = chromadb_service.get_documents(source_collection)
                st.session_state.source_docs = [
                    {
                        'document_id': doc.document_id,
                        'document_name': doc.document_name
                    }
                    for doc in documents
                ]
                st.success(f"Loaded {len(documents)} source documents")
            except Exception as e:
                st.error(f"Failed to load source documents: {e}")

    source_docs = st.session_state.get("source_docs", [])
    source_map = {d["document_name"]: d["document_id"] for d in source_docs}
    selected_sources = st.multiselect(
        "Select Source Document(s)",
        list(source_map.keys()),
        key="gen_sources"
    )
    source_doc_ids = [source_map[name] for name in selected_sources]

    # ----------------------------
    # 3) Let user name the output file
    # ----------------------------
    out_name = st.text_input(
        "Output file name (no extension):",
        value="Generated_Test_Plan",
        key="gen_filename"
    ).strip()

    # ----------------------------
    # 4) Test Card & Export Options
    # ----------------------------
    st.markdown("---")
    st.subheader("Test Card & Export Options")

    col1, col2 = st.columns(2)

    with col1:
        include_test_cards = st.checkbox(
            "Include Test Cards in Generated Document",
            value=True,
            help="Add executable test card tables after each section",
            key="gen_include_test_cards"
        )

    with col2:
        export_method = st.radio(
            "Export Method:",
            ["Standard (python-docx)", "Professional (Pandoc)"],
            horizontal=True,
            help="Pandoc provides better formatting with automatic TOC and section numbering",
            key="gen_export_method"
        )

    # Show Pandoc-specific options if Pandoc is selected
    if "Pandoc" in export_method:
        pandoc_col1, pandoc_col2 = st.columns(2)

        with pandoc_col1:
            include_toc = st.checkbox(
                "Include Table of Contents",
                value=True,
                key="gen_include_toc"
            )

        with pandoc_col2:
            number_sections = st.checkbox(
                "Number Sections Automatically",
                value=True,
                key="gen_number_sections"
            )
    else:
        include_toc = False
        number_sections = False

    st.markdown("---")
    # ----------------------------
    # Resume Existing Pipeline Section
    # ----------------------------
    with st.expander("Resume Existing Generation", expanded=False):
        st.write("If you refreshed the page or came back later, you can resume your generation here.")

        # Show list of pipelines
        try:
            pipelines_response = api_client.get(
                f"{config.endpoints.doc_gen}/list-pipelines",
                timeout=10
            )
            pipelines = pipelines_response.get("pipelines", [])

            if pipelines:
                st.write(f"**Select from {len(pipelines)} recent pipeline(s):**")

                # Create a table of pipelines
                for pipeline in pipelines[:10]:  # Show last 10
                    status = pipeline.get("status", "unknown")
                    pipeline_id = pipeline.get("pipeline_id", "")
                    doc_title = pipeline.get("doc_title", "Untitled")
                    created_at = pipeline.get("created_at", "")

                    # Calculate elapsed time
                    try:
                        from datetime import datetime
                        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        elapsed = datetime.now() - created.replace(tzinfo=None)
                        minutes = int(elapsed.total_seconds() / 60)
                        if minutes < 60:
                            time_str = f"{minutes}m ago"
                        else:
                            hours = minutes // 60
                            time_str = f"{hours}h {minutes % 60}m ago"
                    except:
                        time_str = created_at[:19] if created_at else "Unknown"

                    # Status emoji
                    status_emoji = {
                        "completed": "✅",
                        "processing": "⏳",
                        "queued": "📝",
                        "failed": "❌",
                        "cancelling": "🛑",
                        "initializing": "⏳"
                    }.get(status.lower(), "❓")

                    col1, col2, col3 = st.columns([4, 3, 2])
                    with col1:
                        st.write(f"{status_emoji} **{doc_title}**")
                        st.caption(f"{pipeline_id[:20]}...")
                    with col2:
                        st.write(f"**{status.upper()}**")
                        st.caption(time_str)
                    with col3:
                        button_label = "View" if status.lower() == "completed" else "Resume"
                        button_type = "primary" if status.lower() in ["processing", "queued", "initializing"] else "secondary"
                        if st.button(button_label, key=f"resume_{pipeline_id}", type=button_type, use_container_width=True):
                            st.session_state.pipeline_id = pipeline_id
                            st.query_params["pipeline_id"] = pipeline_id
                            st.rerun()

                    st.markdown("---")

            else:
                st.info("No pipelines found. Start a new generation below.")

        except Exception as e:
            st.warning(f"Could not load pipelines: {e}")
            st.info("Start a new generation below.")


    # ----------------------------
    # Generate Document Button
    # ----------------------------
    st.markdown("---")
    if st.button("Generate Documents (Background)", type="primary", key="generate_docs_async"):
        if not source_doc_ids:
            st.error("You must select at least one source document.")
        else:
            payload = {
                "source_collections": [source_collection],
                "source_doc_ids": source_doc_ids,
                "use_rag": True,
                "top_k": 5,
                "doc_title": out_name,
                "include_test_cards": include_test_cards,
                "export_format": "pandoc" if "Pandoc" in export_method else "python-docx",
                "include_toc": include_toc,
                "number_sections": number_sections
            }

            # Add agent_set_id
            agent_set = next((s for s in active_agent_sets if s['name'] == selected_agent_set), None)
            if agent_set:
                payload["agent_set_id"] = agent_set['id']
                st.info(f"Using agent set: **{selected_agent_set}**")

            try:
                # Call async endpoint
                response = api_client.post(
                    f"{config.endpoints.doc_gen}/generate_documents_async",
                    data=payload,
                    timeout=30  # Quick timeout - just starting the task
                )

                pipeline_id = response.get("pipeline_id")
                if pipeline_id:
                    st.session_state.pipeline_id = pipeline_id
                    st.query_params["pipeline_id"] = pipeline_id
                    st.success(f"Generation started!")
                    st.info(f"Pipeline ID: `{pipeline_id}`")
                    st.info("Refreshing to show progress...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Failed to start generation: No pipeline ID returned")

            except Exception as e:
                st.error(f"Failed to start generation: {e}")
