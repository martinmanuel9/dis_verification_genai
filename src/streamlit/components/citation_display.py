import streamlit as st
from typing import List, Dict, Any, Optional


class CitationDisplay:
    """Unified citation display component with multiple formatting styles"""

    @staticmethod
    def display_simple(
        formatted_citations: str,
        title: str = "Sources and Citations",
        expanded: bool = True,
        caption: Optional[str] = None
    ):
        """
        Display simple pre-formatted citations (Direct Chat style).

        This is for citations that are already formatted as a string by
        the RAG service or other backend services.

        Args:
            formatted_citations: Pre-formatted citation text
            title: Expander title
            expanded: Whether expander is expanded by default
            caption: Optional caption text to display

        Example:
            CitationDisplay.display_simple(
                formatted_citations=result['formatted_citations'],
                title="Sources and Citations"
            )
        """
        if not formatted_citations:
            return

        st.divider()
        with st.expander(title, expanded=expanded):
            st.markdown(formatted_citations)
            if caption:
                st.caption(caption)

    @staticmethod
    def display_structured(
        internal_citations: Optional[List[Dict[str, Any]]] = None,
        external_citations: Optional[List[Dict[str, Any]]] = None,
        formatted_rag_citations: Optional[str] = None,
        formatted_combined_citations: Optional[str] = None
    ):
        """
        Display structured citations with rich metadata (Legal Research style).

        Displays multiple citation types in separate expanders with detailed
        information including quality metrics, excerpts, and metadata.

        Args:
            internal_citations: List of internal document citations
            external_citations: List of external source citations
            formatted_rag_citations: Pre-formatted RAG explainability text
            formatted_combined_citations: Pre-formatted combined citations text

        Example:
            CitationDisplay.display_structured(
                internal_citations=result.get('internal_citations'),
                external_citations=result.get('external_citations'),
                formatted_rag_citations=result.get('formatted_citations_rag')
            )
        """
        # RAG explainability citations
        if formatted_rag_citations:
            with st.expander("Sources and Citations (Explainability)", expanded=True):
                st.markdown(formatted_rag_citations)
                st.caption(
                    "This format shows detailed source provenance from the RAG service, "
                    "including relevance scores and document positions."
                )

        # Combined citations (text format)
        if formatted_combined_citations:
            with st.expander("View All Citations (Combined)", expanded=False):
                st.code(formatted_combined_citations, language='text')

        # Detailed internal citations
        if internal_citations:
            CitationDisplay._display_internal_citations(internal_citations)

        # Detailed external citations
        if external_citations:
            start_idx = (len(internal_citations) + 1) if internal_citations else 1
            CitationDisplay._display_external_citations(external_citations, start_idx=start_idx)

    @staticmethod
    def _display_internal_citations(citations: List[Dict[str, Any]]):
        """
        Display internal citations with rich metadata and quality indicators.

        Args:
            citations: List of internal citation dictionaries
        """
        with st.expander(f"Internal Citations - Detailed Context ({len(citations)})", expanded=True):
            for i, citation in enumerate(citations, 1):
                # Citation header
                doc_name = citation.get('document_name', 'Unknown Document')
                st.markdown(f"### [{i}] {doc_name}")

                # Three-column layout for metadata
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    # Basic metadata
                    if citation.get('collection_name'):
                        st.markdown(f"**Collection**: {citation['collection_name']}")
                    if citation.get('page_number'):
                        st.markdown(f"**Page**: {citation['page_number']}")
                    if citation.get('section_title'):
                        st.markdown(f"**Section**: {citation['section_title']}")

                with col2:
                    # Document position information
                    if citation.get('chunk_index') is not None and citation.get('total_chunks'):
                        chunk_idx = citation['chunk_index']
                        total_chunks = citation['total_chunks']
                        st.markdown(f"**Location**: Chunk {chunk_idx + 1} of {total_chunks}")

                    if citation.get('position_indicator'):
                        st.markdown(f"**Position**: {citation['position_indicator']}")

                with col3:
                    # Quality/relevance indicators
                    if citation.get('quality_tier'):
                        quality = citation['quality_tier']
                        quality_emoji = {
                            'Excellent': '🟢',
                            'High': '🟢',
                            'Good': '🟡',
                            'Fair': '🟡',
                            'Low': '🔴'
                        }.get(quality, '⚪')
                        st.metric("Quality", f"{quality_emoji} {quality}")
                    elif citation.get('relevance_score') is not None:
                        score = citation['relevance_score']
                        st.metric("Distance", f"{score:.2f}")

                # Excerpt display
                if citation.get('excerpt'):
                    st.markdown("**Excerpt:**")
                    excerpt_text = citation['excerpt']

                    # Collapsible for long excerpts
                    if len(excerpt_text) > 500:
                        with st.expander("View full excerpt", expanded=False):
                            st.info(excerpt_text)
                    else:
                        st.info(excerpt_text)

                # Visual separator between citations
                if i < len(citations):
                    st.markdown("---")

    @staticmethod
    def _display_external_citations(citations: List[Dict[str, Any]], start_idx: int = 1):
        """
        Display external citations with URLs and legal metadata.

        Args:
            citations: List of external citation dictionaries
            start_idx: Starting index for citation numbering
        """
        with st.expander(f"External Citations - Case Law & Legal Sources ({len(citations)})", expanded=True):
            for i, citation in enumerate(citations, start_idx):
                # Citation header
                doc_name = citation.get('document_name', 'Unknown Source')
                st.markdown(f"### [{i}] {doc_name}")

                # Two-column layout
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Legal citation format
                    if citation.get('citation_format'):
                        st.markdown(f"**Citation**: {citation['citation_format']}")

                    # URL with source indicator
                    if citation.get('url'):
                        source = citation.get('metadata', {}).get('source', 'Web')
                        st.markdown(f"**Source**: [View on {source}]({citation['url']})")

                    # Legal metadata
                    if citation.get('metadata'):
                        metadata = citation['metadata']
                        if metadata.get('court'):
                            st.markdown(f"**Court**: {metadata['court']}")
                        if metadata.get('date'):
                            st.markdown(f"**Date**: {metadata['date']}")
                        if metadata.get('jurisdiction'):
                            st.markdown(f"**Jurisdiction**: {metadata['jurisdiction']}")

                with col2:
                    # Relevance score
                    if citation.get('relevance_score') is not None and citation['relevance_score'] > 0:
                        relevance = citation['relevance_score'] * 100
                        st.metric("Relevance", f"{relevance:.0f}%")

                # Excerpt display
                if citation.get('excerpt'):
                    st.markdown("**Excerpt:**")
                    excerpt_text = citation['excerpt']

                    if len(excerpt_text) > 500:
                        with st.expander("View full excerpt", expanded=False):
                            st.info(excerpt_text)
                    else:
                        st.info(excerpt_text)

                # Visual separator between citations
                if i < start_idx + len(citations) - 1:
                    st.markdown("---")

    @staticmethod
    def display_compact(
        citations: List[Dict[str, Any]],
        title: str = "Citations",
        show_quality: bool = True
    ):
        """
        Display citations in a compact table format.

        Useful for showing multiple citations in a space-efficient manner.

        Args:
            citations: List of citation dictionaries
            title: Section title
            show_quality: Whether to show quality indicators

        Example:
            CitationDisplay.display_compact(
                citations=internal_citations,
                title="Referenced Documents"
            )
        """
        if not citations:
            return

        st.subheader(title)

        # Prepare table data
        table_data = []
        for i, cite in enumerate(citations, 1):
            row = {
                "#": i,
                "Document": cite.get('document_name', 'Unknown')[:50],
                "Page": cite.get('page_number', 'N/A')
            }

            if show_quality and cite.get('quality_tier'):
                quality = cite.get('quality_tier')
                emoji = {'Excellent': '🟢', 'High': '🟢', 'Good': '🟡', 'Fair': '🟡', 'Low': '🔴'}.get(quality, '⚪')
                row["Quality"] = f"{emoji} {quality}"

            table_data.append(row)

        st.table(table_data)

    @staticmethod
    def display_footnotes(
        citations: List[Dict[str, Any]],
        text_with_markers: str
    ):
        """
        Display text with citation markers and footnotes.

        Args:
            citations: List of citation dictionaries
            text_with_markers: Text containing citation markers like [1], [2], etc.

        Example:
            CitationDisplay.display_footnotes(
                citations=citations,
                text_with_markers="The evidence shows [1] that the defendant [2]..."
            )
        """
        # Display main text with markers
        st.markdown(text_with_markers)

        # Display footnotes
        if citations:
            st.markdown("---")
            st.markdown("**References:**")

            for i, cite in enumerate(citations, 1):
                doc_name = cite.get('document_name', 'Unknown')
                page = cite.get('page_number')

                ref_text = f"[{i}] {doc_name}"
                if page:
                    ref_text += f", p. {page}"

                if cite.get('url'):
                    st.markdown(f"{ref_text} - [Link]({cite['url']})")
                else:
                    st.markdown(ref_text)


# Export singleton instance for convenience
citation_display = CitationDisplay()
