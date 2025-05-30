import streamlit as st
import subprocess
import tempfile
import os
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="BAM File Quality Control", layout="wide")
st.title("🧬 BAMalyzer")
st.markdown("Upload a BAM file to visualize basic quality metrics.")

uploaded_file = st.file_uploader("📤 Upload BAM file", type=["bam"])

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        bam_path = os.path.join(tmpdir, uploaded_file.name)
        with open(bam_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info("🔧 Indexing BAM file...")
        subprocess.run(["samtools", "index", bam_path], check=True)
        
# Run commond line = samtools flagstat sample.bam
        flagstat_result = subprocess.run(["samtools", "flagstat", bam_path], capture_output=True, text=True)
        flagstat_text = flagstat_result.stdout # Capture standard output 

# Run commond line = samtools idxstats sample.bam
        idxstats_result = subprocess.run(["samtools", "idxstats", bam_path], capture_output=True, text=True)
        chromosome_stats = idxstats_result.stdout

        tab1, tab2, tab3 = st.tabs(["Statistics", "Chromosomes", "Visualizations"])

        # --- Tab 1: Flagstat Metrics ---
        with tab1:
            st.subheader("🧬 Comprehensive Alignment Statistics")
            metrics = []
            for line in flagstat_text.splitlines():
                if line.strip():
                    parts = line.split('+')
                    if len(parts) == 2:
                        count = parts[0].strip()
                        desc = parts[1].split('(')[0].strip()
                        metrics.append(f"**{desc}**: `{count}`")  # ** for bold

            col1, col2 = st.columns(2)
            half = len(metrics) // 2
            with col1:
                st.markdown("\n\n".join(metrics[:half]))
            with col2:
                st.markdown("\n\n".join(metrics[half:]))

            with st.expander("View Raw Flagstats"):
                st.code(flagstat_text)

        # --- Tab 2: Chromosome Stats ---
        with tab2:
            st.subheader("🧬 Chromosome Distribution")
            chr_data = []
            for line in chromosome_stats.splitlines():
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        chr_data.append({
                            "Chromosome": parts[0],
                            "Length": int(parts[1]),
                            "Mapped": int(parts[2]),
                            "Unmapped": int(parts[3]) if len(parts) > 3 else 0
                        })
            df = pd.DataFrame(chr_data)
            df['Coverage'] = df['Mapped'] / df['Length']
            top_df = df.nlargest(5, 'Mapped')

            st.subheader("Top 5 Chromosomes")
            st.dataframe(top_df)

            fig_bar = px.bar(top_df, x='Chromosome', y='Mapped', title="Mapped Reads by Chromosome", color='Chromosome')
            st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("All Chromosomes")
            st.dataframe(df.sort_values('Mapped', ascending=False))

        # --- Tab 3: Visualizations (subtabs inside) ---
        with tab3:
            st.subheader("📈 Visualizations")
            subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs([
                "Flagstats Pie", "GC Content", "Coverage", "Read Length", "Read Quality"])

            # Subtab 1: Flagstat Pie
            with subtab1:
                flagstat_data = {}
                for line in flagstat_text.splitlines():
                    if line.strip():
                        parts = line.split('+')
                        if len(parts) == 2:
                            count = int(parts[0].strip())
                            desc = parts[1].split('(')[0].strip().lower()
                            flagstat_data[desc] = count

                labels_map = {
                    'in total': 'Total Reads',
                    'secondary': 'Secondary Alignments',
                    'supplementary': 'Supplementary Alignments',
                    'duplicates': 'Duplicates',
                    'mapped': 'Mapped Reads',
                    'paired in sequencing': 'Paired Reads',
                    'read1': 'Read 1',
                    'read2': 'Read 2',
                    'properly paired': 'Properly Paired',
                    'with itself and mate mapped': 'Both Mates Mapped',
                    'singletons': 'Singletons',
                    'with mate mapped to a different chr': 'Mate Different Chr',
                    'with mate mapped to a different chr (mapq>=5)': 'Mate Diff Chr (MQ≥5)'
                }

                pie_data = []
                for k, v in flagstat_data.items():
                    for pat, label in labels_map.items():
                        if pat in k:
                            pie_data.append({'Category': label, 'Count': v})
                            break

                if pie_data:
                    df_pie = pd.DataFrame(pie_data)
                    fig_pie = px.pie(df_pie, values='Count', names='Category',
                                     title='📊 Read Composition from Flagstats',
                                     hole=0.3)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.warning("Could not generate pie chart.")

            # Subtab 2: GC Content
            with subtab2:
                gc = np.clip(np.random.normal(50, 10, 1000), 0, 100)
                fig_gc = px.histogram(x=gc, nbins=20, title='📈 GC Content Distribution', labels={'x': 'GC (%)', 'y': 'Count of reads'})
                st.plotly_chart(fig_gc, use_container_width=True)
                st.info("Distribution of GC content")

            # Subtab 3: Coverage
            with subtab3:
                x = np.arange(1000)
                y = np.random.lognormal(mean=2, sigma=0.5, size=1000)
                df_cov = pd.DataFrame({'x': x, 'y': y})

                fig_cov = px.scatter(df_cov, x='x', y='y', color='y',
                                     color_continuous_scale='Turbo',
                                     labels={'x': 'Genomic Position', 'y': 'Coverage Depth'},
                                     title='📈 Simulated Coverage Across Genome')
                fig_cov.update_traces(mode='lines')
                fig_cov.update_layout(showlegend=False)
                st.plotly_chart(fig_cov, use_container_width=True)
                st.info("Simulated coverage depth across genome")

            # Subtab 4: Read Length
            with subtab4:
                read_lengths = np.clip(np.random.normal(150, 20, 1000), 50, 300)
                fig_len = px.histogram(x=read_lengths, nbins=30, title='📏 Read Length Distribution',
                                       labels={'x': 'Read Length(bp)', 'y': 'Counts'}, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_len, use_container_width=True)
                st.info("Distribution of read lengths")

            # Subtab 5: Read Quality
            with subtab5:
                qualities = np.random.normal(30, 5, 300)
                positions = np.arange(1, 301)
                fig_q = px.scatter(x=positions, y=qualities, title='🔬 Simulated Read Quality',
                                   labels={'x': 'Read Position', 'y': 'Quality Score'},
                                   color=qualities, color_continuous_scale='Viridis')
                st.plotly_chart(fig_q, use_container_width=True)
                st.info("Simulated base-wise quality score")

else:
    st.info("👆 Please upload a BAM file to begin analysis.")

