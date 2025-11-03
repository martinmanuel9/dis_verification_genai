"""
RAG Assessment Dashboard Component
Migrated to new architecture - uses centralized config and services

Comprehensive RAG performance monitoring and analytics dashboard with:
- Live RAG Assessment with quality metrics
- Performance Analytics
- Configuration Benchmarking
- Collection Analysis
- Export & Reports
"""
import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any
import base64

from config.settings import config
from lib.api.client import api_client
from services.chromadb_service import chromadb_service


def rag_assessment_dashboard():
    """
    RAG Assessment Service Dashboard - Comprehensive RAG performance monitoring and analytics
    """
    st.header("RAG Assessment Service (RAGAS)")
    st.info("Monitor, evaluate, and optimize RAG performance with comprehensive metrics and analytics.")

    # Health check
    try:
        health_response = api_client.get(
            f"{config.endpoints.health}/rag-health",
            timeout=5,
            show_errors=False
        )
        active_sessions = health_response.get('metrics', {}).get('active_sessions', 0)
        st.success(f"RAG Assessment Service is healthy - {active_sessions} sessions tracked")
    except Exception as e:
        st.warning(f"RAG Assessment Service health check failed: {str(e)}")
        # Continue anyway - service might still be functional

    # Main tabs
    assessment_tab, analytics_tab, benchmark_tab, collections_tab, export_tab = st.tabs([
        "Live Assessment",
        "Performance Analytics",
        "Benchmarking",
        "Collection Analysis",
        "Export & Reports"
    ])

    # ===== LIVE ASSESSMENT TAB =====
    with assessment_tab:
        _render_live_assessment_tab()

    # ===== ANALYTICS TAB =====
    with analytics_tab:
        _render_analytics_tab()

    # ===== BENCHMARKING TAB =====
    with benchmark_tab:
        _render_benchmarking_tab()

    # ===== COLLECTIONS TAB =====
    with collections_tab:
        _render_collections_tab()

    # ===== EXPORT TAB =====
    with export_tab:
        _render_export_tab()


def _render_live_assessment_tab():
    """Render the Live Assessment tab"""
    st.subheader("Live RAG Assessment")
    st.info("Test individual queries with comprehensive performance and quality metrics.")

    # Load collections
    try:
        collections = chromadb_service.get_collections()
    except Exception as e:
        st.error(f"Failed to load collections: {e}")
        collections = []

    col1, col2 = st.columns([2, 1])

    with col1:
        query_text = st.text_area(
            "Query for RAG Assessment:",
            placeholder="e.g., 'What are the key compliance requirements in this contract?'",
            height=100,
            key="rag_assessment_query"
        )

    with col2:
        if collections:
            collection_name = st.selectbox(
                "Select Collection:",
                collections,
                key="rag_assessment_collection"
            )
        else:
            st.warning("No collections available")
            collection_name = None

        model_name = st.selectbox(
            "Model:",
            ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            key="rag_assessment_model"
        )

        top_k = st.slider("Top K Documents:", 1, 20, 5, key="rag_assessment_top_k")

        include_quality = st.checkbox("Include Quality Assessment", value=True, key="rag_quality_check")

    if st.button("Run RAG Assessment", type="primary", key="run_rag_assessment"):
        if not query_text:
            st.warning("Please enter a query.")
        elif not collection_name:
            st.warning("Please select a collection.")
        else:
            with st.spinner("Performing comprehensive RAG assessment..."):
                try:
                    payload = {
                        "query": query_text,
                        "collection_name": collection_name,
                        "model_name": model_name,
                        "top_k": top_k,
                        "include_quality_assessment": include_quality
                    }

                    result = api_client.post(
                        f"{config.endpoints.api}/rag/assessment",
                        data=payload,
                        timeout=300
                    )

                    # Display response
                    st.success("RAG Assessment Complete!")

                    # Response content
                    st.subheader("Generated Response")
                    st.markdown(result["response"])

                    # Performance metrics
                    st.subheader("Performance Metrics")
                    perf = result["performance_metrics"]

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Time", f"{perf['total_time_ms']:.1f}ms")
                    with col2:
                        st.metric("Retrieval Time", f"{perf['retrieval_time_ms']:.1f}ms")
                    with col3:
                        st.metric("Generation Time", f"{perf['generation_time_ms']:.1f}ms")
                    with col4:
                        st.metric("Documents Retrieved", perf['documents_retrieved'])

                    # Performance breakdown chart
                    perf_data = {
                        'Phase': ['Retrieval', 'Generation'],
                        'Time (ms)': [perf['retrieval_time_ms'], perf['generation_time_ms']]
                    }

                    fig = px.bar(
                        perf_data,
                        x='Phase',
                        y='Time (ms)',
                        title="Performance Breakdown",
                        color='Phase'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Quality assessment
                    if result.get("quality_assessment"):
                        st.subheader("Quality Assessment")
                        quality = result["quality_assessment"]

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Overall Quality", f"{quality['overall_quality']:.2f}")
                            st.metric("Relevance", f"{quality['relevance_score']:.2f}")
                        with col2:
                            st.metric("Coherence", f"{quality['coherence_score']:.2f}")
                            st.metric("Completeness", f"{quality['completeness_score']:.2f}")
                        with col3:
                            st.metric("Factual Accuracy", f"{quality['factual_accuracy']:.2f}")
                            st.metric("Context Utilization", f"{quality['context_utilization']:.2f}")

                        # Quality radar chart
                        fig = go.Figure()

                        categories = ['Relevance', 'Coherence', 'Factual Accuracy',
                                    'Completeness', 'Context Utilization']
                        values = [
                            quality['relevance_score'],
                            quality['coherence_score'],
                            quality['factual_accuracy'],
                            quality['completeness_score'],
                            quality['context_utilization']
                        ]

                        fig.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name='Quality Metrics'
                        ))

                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 1]
                                )),
                            showlegend=True,
                            title="Quality Assessment Radar"
                        )

                        st.plotly_chart(fig, use_container_width=True)

                    # Session details
                    with st.expander("Detailed Metrics"):
                        st.json(result)

                    # Word Export Section
                    st.markdown("---")
                    st.subheader("Export Assessment Results")
                    if st.button("Export to Word", type="secondary", key="export_rag_assessment"):
                        try:
                            with st.spinner("Generating Word document..."):
                                export_response = api_client.post(
                                    f"{config.endpoints.doc_gen}/export-rag-assessment-word",
                                    data=result,
                                    timeout=30
                                )

                                file_content = export_response.get("content_b64")
                                filename = export_response.get("filename", "rag_assessment_export.docx")

                                if file_content:
                                    doc_bytes = base64.b64decode(file_content)

                                    st.download_button(
                                        label=f"Download {filename}",
                                        data=doc_bytes,
                                        file_name=filename,
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key="download_rag_assessment"
                                    )
                                    st.success("RAG assessment exported successfully!")
                                else:
                                    st.error("No file content received")
                        except Exception as e:
                            st.error(f"Error exporting RAG assessment: {str(e)}")

                except Exception as e:
                    st.error(f"Assessment error: {str(e)}")


def _render_analytics_tab():
    """Render the Performance Analytics tab"""
    st.subheader("Performance Analytics")
    st.info("View comprehensive performance analytics across time periods.")

    # Load collections
    try:
        collections = chromadb_service.get_collections()
    except Exception:
        collections = []

    col1, col2 = st.columns([1, 1])

    with col1:
        time_period = st.selectbox(
            "Analysis Period:",
            [1, 6, 12, 24, 48, 168],  # hours
            format_func=lambda x: f"{x} hours" if x < 24 else f"{x//24} days",
            index=3,  # default to 24 hours
            key="analytics_time_period"
        )

    with col2:
        analytics_collection = st.selectbox(
            "Filter by Collection:",
            ["All Collections"] + (collections if collections else []),
            key="analytics_collection_filter"
        )

    if st.button("Generate Analytics Report", key="generate_analytics"):
        with st.spinner("Generating comprehensive analytics report..."):
            try:
                payload = {
                    "time_period_hours": time_period,
                    "collection_name": analytics_collection if analytics_collection != "All Collections" else None
                }

                analytics = api_client.post(
                    f"{config.endpoints.api}/rag/analytics",
                    data=payload,
                    timeout=60
                )

                if "message" in analytics:
                    st.warning(analytics["message"])
                else:
                    st.success("Analytics Report Generated!")

                    # Overview metrics
                    st.subheader("Overview")
                    query_stats = analytics["query_statistics"]

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Queries", query_stats["total_queries"])
                    with col2:
                        st.metric("Success Rate", f"{query_stats['success_rate']:.1%}")
                    with col3:
                        st.metric("Successful", query_stats["successful_queries"])
                    with col4:
                        st.metric("Failed", query_stats["failed_queries"])

                    # Performance metrics
                    st.subheader("Performance Metrics")
                    perf_metrics = analytics["performance_metrics"]

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Avg Response Time",
                            f"{perf_metrics['response_time_ms']['mean']:.1f}ms"
                        )
                        st.metric(
                            "Median Response Time",
                            f"{perf_metrics['response_time_ms']['median']:.1f}ms"
                        )
                    with col2:
                        st.metric(
                            "Avg Retrieval Time",
                            f"{perf_metrics['retrieval_time_ms']['mean']:.1f}ms"
                        )
                        st.metric(
                            "Avg Generation Time",
                            f"{perf_metrics['generation_time_ms']['mean']:.1f}ms"
                        )
                    with col3:
                        st.metric(
                            "Min Response Time",
                            f"{perf_metrics['response_time_ms']['min']:.1f}ms"
                        )
                        st.metric(
                            "Max Response Time",
                            f"{perf_metrics['response_time_ms']['max']:.1f}ms"
                        )

                    # Usage patterns
                    st.subheader("Usage Patterns")
                    usage = analytics["usage_patterns"]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Collections Used:**")
                        for collection in usage["collections_used"]:
                            st.write(f"• {collection}")

                        st.metric("Avg Documents Retrieved", f"{usage['avg_documents_retrieved']:.1f}")

                    with col2:
                        st.write("**Models Used:**")
                        for model in usage["models_used"]:
                            st.write(f"• {model}")

                        st.metric("Avg Response Length", f"{usage['avg_response_length']:.0f} chars")

                    # Quality metrics (if available)
                    if "quality_metrics" in analytics and analytics["quality_metrics"]["overall_quality"]["samples"] > 0:
                        st.subheader("Quality Metrics")
                        quality = analytics["quality_metrics"]["overall_quality"]

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Avg Quality Score", f"{quality['mean']:.2f}")
                        with col2:
                            st.metric("Median Quality", f"{quality['median']:.2f}")
                        with col3:
                            st.metric("Quality Samples", quality['samples'])

                    # Raw analytics data
                    with st.expander("Raw Analytics Data"):
                        st.json(analytics)

            except Exception as e:
                st.error(f"Analytics error: {str(e)}")


def _render_benchmarking_tab():
    """Render the Benchmarking tab"""
    st.subheader("RAG Configuration Benchmarking")
    st.info("Compare different RAG configurations on standardized query sets.")

    # Load collections
    try:
        collections = chromadb_service.get_collections()
    except Exception:
        collections = []

    # Benchmark setup
    st.write("**Step 1: Define Test Queries**")
    benchmark_queries = st.text_area(
        "Test Queries (one per line):",
        placeholder="What are the compliance requirements?\nAnalyze contract risks\nSummarize key terms",
        height=100,
        key="benchmark_queries"
    )

    st.write("**Step 2: Select Collection**")
    if collections:
        benchmark_collection = st.selectbox(
            "Benchmark Collection:",
            collections,
            key="benchmark_collection"
        )
    else:
        st.warning("No collections available for benchmarking")
        benchmark_collection = None

    st.write("**Step 3: Configure Test Scenarios**")

    # Configuration builder
    config_expander = st.expander("➕ Configuration Builder", expanded=True)
    with config_expander:
        col1, col2, col3 = st.columns(3)

        with col1:
            config_model = st.selectbox(
                "Model:",
                ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                key="config_model"
            )

        with col2:
            config_top_k = st.slider("Top K:", 1, 20, 5, key="config_top_k")

        with col3:
            if st.button("➕ Add Configuration", key="add_config"):
                new_config = {
                    "model_name": config_model,
                    "top_k": config_top_k
                }
                if "benchmark_configs" not in st.session_state:
                    st.session_state.benchmark_configs = []
                st.session_state.benchmark_configs.append(new_config)
                st.success(f"Added: {config_model} (top_k={config_top_k})")
                st.rerun()

    # Display configured scenarios
    if "benchmark_configs" in st.session_state and st.session_state.benchmark_configs:
        st.write("**Configured Test Scenarios:**")
        for i, cfg in enumerate(st.session_state.benchmark_configs):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**Config {i+1}:** {cfg['model_name']} (top_k={cfg['top_k']})")
            with col2:
                if st.button("X", key=f"remove_config_{i}", help="Remove this configuration"):
                    st.session_state.benchmark_configs.pop(i)
                    st.rerun()

    # Run benchmark
    if st.button("Run Benchmark", type="primary", key="run_benchmark"):
        if not benchmark_queries:
            st.warning("Please provide test queries.")
        elif not benchmark_collection:
            st.warning("Please select a collection.")
        elif "benchmark_configs" not in st.session_state or not st.session_state.benchmark_configs:
            st.warning("Please add at least one configuration.")
        else:
            query_list = [q.strip() for q in benchmark_queries.split('\n') if q.strip()]

            with st.spinner(f"Running benchmark with {len(query_list)} queries across {len(st.session_state.benchmark_configs)} configurations..."):
                try:
                    payload = {
                        "query_set": query_list,
                        "collection_name": benchmark_collection,
                        "configurations": st.session_state.benchmark_configs
                    }

                    results = api_client.post(
                        f"{config.endpoints.api}/rag/benchmark",
                        data=payload,
                        timeout=600  # 10 minutes for benchmarking
                    )

                    st.success("Benchmark Complete!")

                    # Results overview
                    st.subheader("Benchmark Results")

                    benchmark_data = []
                    for config_id, result in results["results"].items():
                        cfg = result["configuration"]
                        metrics = result["results"]

                        benchmark_data.append({
                            "Configuration": f"{cfg['model_name']} (k={cfg['top_k']})",
                            "Avg Response Time (ms)": metrics["avg_response_time_ms"],
                            "Avg Quality Score": metrics.get("avg_quality_score", 0),
                            "Queries Tested": metrics["queries_tested"]
                        })

                    # Results table
                    df = pd.DataFrame(benchmark_data)
                    st.dataframe(df, use_container_width=True)

                    # Performance comparison chart
                    fig = px.scatter(
                        df,
                        x="Avg Response Time (ms)",
                        y="Avg Quality Score",
                        text="Configuration",
                        title="Performance vs Quality Trade-off",
                        hover_data=["Queries Tested"]
                    )
                    fig.update_traces(textposition="top center")
                    st.plotly_chart(fig, use_container_width=True)

                    # Detailed results
                    with st.expander("Detailed Benchmark Results"):
                        st.json(results)

                except Exception as e:
                    st.error(f"Benchmark error: {str(e)}")


def _render_collections_tab():
    """Render the Collection Analysis tab"""
    st.subheader("Collection Analysis")
    st.info("Analyze RAG performance by collection.")

    try:
        collections = chromadb_service.get_collections()
    except Exception as e:
        st.error(f"Failed to load collections: {e}")
        return

    if not collections:
        st.warning("No collections available for analysis.")
        return

    selected_collection = st.selectbox(
        "Select Collection for Analysis:",
        collections,
        key="collection_analysis_select"
    )

    if st.button("Analyze Collection", key="analyze_collection"):
        with st.spinner(f"Analyzing collection: {selected_collection}..."):
            try:
                # Get collection statistics
                documents = chromadb_service.get_documents(selected_collection)

                st.success(f"Collection Analysis: {selected_collection}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Documents", len(documents))
                with col2:
                    total_chunks = sum(doc.total_chunks for doc in documents)
                    st.metric("Total Chunks", total_chunks)
                with col3:
                    avg_chunks = total_chunks / len(documents) if documents else 0
                    st.metric("Avg Chunks/Doc", f"{avg_chunks:.1f}")

                # File type distribution
                file_types = {}
                for doc in documents:
                    file_type = doc.file_type or 'unknown'
                    file_types[file_type] = file_types.get(file_type, 0) + 1

                st.subheader("File Type Distribution")
                fig = px.pie(
                    values=list(file_types.values()),
                    names=list(file_types.keys()),
                    title="Documents by File Type"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Document list
                st.subheader("Documents in Collection")
                doc_data = [
                    {
                        "Name": doc.document_name,
                        "Type": doc.file_type,
                        "Chunks": doc.total_chunks,
                        "Has Images": "Yes" if doc.has_images else "No"
                    }
                    for doc in documents
                ]
                st.dataframe(pd.DataFrame(doc_data), use_container_width=True)

            except Exception as e:
                st.error(f"Collection analysis error: {str(e)}")


def _render_export_tab():
    """Render the Export & Reports tab"""
    st.subheader("Export & Reports")
    st.info("Export RAG assessment data and generate comprehensive reports.")

    st.write("**Available Export Options:**")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**1. Export Analytics Report**")
        if st.button("Export Analytics to CSV", key="export_analytics_csv"):
            st.info("Analytics export feature coming soon.")

    with col2:
        st.write("**2. Export Benchmark Results**")
        if st.button("Export Benchmarks to CSV", key="export_benchmarks_csv"):
            st.info("Benchmark export feature coming soon.")

    st.markdown("---")
    st.write("**Session History Export**")
    if st.button("Export Session History", key="export_session_history"):
        st.info("Session history export feature coming soon.")
