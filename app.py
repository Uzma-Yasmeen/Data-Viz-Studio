# --------------------------------------------------
# 📊 DataViz Studio: An Interactive Data Analytics Dashboard
# --------------------------------------------------

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import io

# --- Streamlit setup ---
st.set_page_config(page_title="DataViz Studio", layout="wide")
st.title("📊 DataViz Studio: An Interactive Data Analytics Dashboard")

# --- Helper: Make DataFrame Arrow-safe for st.dataframe ---
def arrow_safe_df(df):
    df_copy = df.copy()
    for col in df_copy.columns:
        # Nullable integer -> float
        if pd.api.types.is_integer_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].astype(float)
        # Mixed / object -> string
        elif pd.api.types.is_object_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].astype(str)
    return df_copy

# --- File upload ---
st.sidebar.header("📂 Upload Your Dataset")
uploaded_file = st.sidebar.file_uploader("Upload a data file", type=["csv", "json", "xlsx"])

MAX_POINTS = 1000  # For large dataset sampling

if uploaded_file is not None:
    # --- Robust file loading ---
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".json"):
            try:
                df = pd.read_json(uploaded_file)  # Standard JSON
            except ValueError:
                uploaded_file.seek(0)
                df = pd.read_json(uploaded_file, lines=True)  # JSON lines
        elif uploaded_file.name.endswith(".xlsx"):
            try:
                df = pd.read_excel(uploaded_file, sheet_name=0)  # First sheet
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {e}")
                st.stop()
        else:
            st.error("❌ Unsupported file type.")
            st.stop()
        st.success(f"✅ Successfully loaded **{uploaded_file.name}**")
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        st.stop()

    # --- Large dataset optimization ---
    plot_df = df.copy()
    if plot_df.shape[0] > MAX_POINTS:
        plot_df = plot_df.sample(n=MAX_POINTS, random_state=42)
        st.info(f"ℹ️ Dataset sampled to {MAX_POINTS} rows for visualization.")

    # --- Display DataFrame safely ---
    st.dataframe(arrow_safe_df(plot_df.head()))

    if "graphs" not in st.session_state:
        st.session_state["graphs"] = []

    # --- EDA Section ---
    with st.expander("📈 Explore Dataset"):
        st.write("### Dataset Summary")
        st.dataframe(arrow_safe_df(plot_df.describe().T))

        st.write("### Missing Values")
        st.dataframe(arrow_safe_df(plot_df.isnull().sum().to_frame("Missing Values")))

        st.write("### Column Data Types")
        st.dataframe(arrow_safe_df(plot_df.dtypes.to_frame("Data Type")))

        # Correlation heatmap for numeric columns
        numeric_df = plot_df.select_dtypes(include=["number"])
        if numeric_df.shape[1] > 1:
            st.write("### 🔥 Correlation Heatmap")
            corr = numeric_df.corr()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax, fmt=".2f", linewidths=0.5)
            ax.set_title("Correlation Matrix", fontsize=12, fontweight="bold")
            st.pyplot(fig)
        else:
            st.info("ℹ️ Not enough numeric columns for correlation analysis.")

    # --- Visualization Section ---
    st.sidebar.header("🎨 Create Visualizations")
    x_axis = st.sidebar.selectbox("Select X-axis", plot_df.columns)
    y_axis = st.sidebar.selectbox("Select Y-axis", plot_df.columns)
    graph_type = st.sidebar.selectbox(
        "Select Graph Type",
        ["Line", "Bar", "Scatter", "Histogram", "Boxplot", "Pie", "Heatmap", "Pairplot", "Regression"]
    )
    graph_size = st.sidebar.slider("Graph Size (Adjust Zoom)", 4, 16, 8)

    # Color customization
    main_color = st.sidebar.color_picker("Main Color", "#1f77b4")
    edge_color = st.sidebar.color_picker("Edge/Outline Color", "#000000")

    # --- Helper: Check compatibility ---
    numeric_types = ["int64", "float64"]
    x_dtype = plot_df[x_axis].dtype
    y_dtype = plot_df[y_axis].dtype

    def check_plot_compatibility():
        if graph_type in ["Line", "Scatter", "Histogram", "Boxplot", "Regression"]:
            if x_dtype not in numeric_types and graph_type not in ["Histogram", "Boxplot"]:
                st.error(f"❌ X-axis '{x_axis}' must be numeric for {graph_type} plot.")
                st.stop()
            if y_dtype not in numeric_types and graph_type not in ["Histogram", "Boxplot"]:
                st.error(f"❌ Y-axis '{y_axis}' must be numeric for {graph_type} plot.")
                st.stop()
        elif graph_type == "Pie":
            if x_dtype in numeric_types and plot_df[x_axis].nunique() > 15:
                st.warning("⚠️ Pie chart works best for categorical columns or few unique values.")
                st.stop()
        elif graph_type == "Regression":
            if x_dtype not in numeric_types or y_dtype not in numeric_types:
                st.error("❌ Both X and Y must be numeric for Regression.")
                st.stop()

    check_plot_compatibility()

    # --- Generate Graph ---
    if st.sidebar.button("Generate Graph"):
        fig, ax = plt.subplots(figsize=(graph_size, graph_size / 1.5))
        try:
            if graph_type == "Line":
                ax.plot(plot_df[x_axis], plot_df[y_axis], color=main_color, linewidth=2)
            elif graph_type == "Bar":
                ax.bar(plot_df[x_axis], plot_df[y_axis], color=main_color, edgecolor=edge_color)
            elif graph_type == "Scatter":
                ax.scatter(plot_df[x_axis], plot_df[y_axis], color=main_color, edgecolors=edge_color, s=60)
            elif graph_type == "Histogram":
                ax.hist(plot_df[x_axis], bins=20, color=main_color, edgecolor=edge_color, alpha=0.7)
            elif graph_type == "Boxplot":
                ax.boxplot(plot_df[y_axis].dropna(), boxprops=dict(color=main_color), medianprops=dict(color=edge_color))
                ax.set_xticklabels([y_axis])
            elif graph_type == "Pie":
                data = plot_df[x_axis].value_counts()
                ax.pie(data.values, labels=data.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.tab10.colors)
                ax.set_title(f"Pie Chart of {x_axis}")
                ax.axis("equal")
            elif graph_type == "Heatmap":
                numeric_df = plot_df.select_dtypes(include=["number"])
                sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
                ax.set_title("Correlation Heatmap")
            elif graph_type == "Pairplot":
                numeric_df = plot_df.select_dtypes(include=["number"])
                pair_fig = sns.pairplot(numeric_df)
                st.pyplot(pair_fig)
                st.stop()
            elif graph_type == "Regression":
                sns.regplot(x=plot_df[x_axis], y=plot_df[y_axis], ax=ax, color=main_color)

            ax.set_xlabel(x_axis)
            if graph_type != "Pie":
                ax.set_ylabel(y_axis)
            ax.set_title(f"{graph_type} of {y_axis} vs {x_axis}" if graph_type != "Pie" else f"{graph_type} of {x_axis}")

            st.pyplot(fig)
            st.session_state["graphs"].append((fig, f"{graph_type} of {y_axis} vs {x_axis}"))

        except Exception as e:
            st.error(f"Error: {e}")

    # --- Combined Dashboard ---
    if st.session_state["graphs"]:
        st.subheader("🧩 Combined Dashboard View")

        num_graphs = len(st.session_state["graphs"])
        cols = 2 if num_graphs >= 4 else 1
        rows = (num_graphs + cols - 1) // cols

        fig, axs = plt.subplots(rows, cols, figsize=(10, 5 * rows))
        axs = axs.flatten() if num_graphs > 1 else [axs]

        for i, (graph_data, ax_slot) in enumerate(zip(st.session_state["graphs"], axs)):
            graph, _ = graph_data
            graph.canvas.draw()
            img = np.asarray(graph.canvas.buffer_rgba())
            ax_slot.imshow(img)
            ax_slot.axis("off")
            ax_slot.set_title(f"Graph {i+1}", fontsize=10)

        for j in range(i + 1, len(axs)):
            fig.delaxes(axs[j])

        plt.tight_layout()
        st.pyplot(fig)

        # --- Individual Graph Downloads ---
        st.subheader("📥 Download Individual Graphs")
        for i, (graph, title) in enumerate(st.session_state["graphs"]):
            buf = io.BytesIO()
            graph.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            st.download_button(
                label=f"Download Graph {i+1}: {title}",
                data=buf,
                file_name=f"{title.replace(' ', '_')}.png",
                mime="image/png"
            )

        # --- Combined PDF Report ---
        pdf_buffer = BytesIO()
        with PdfPages(pdf_buffer) as pdf:
            # Page 1: Stats and Overview
            stats_fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis("off")
            ax.text(0.5, 0.95, "📊 DataViz Studio Report", fontsize=18, fontweight="bold", ha="center")
            ax.text(0.05, 0.90, f"File Name: {uploaded_file.name}", fontsize=11)
            ax.text(0.05, 0.87, f"Rows: {df.shape[0]}    Columns: {df.shape[1]}", fontsize=11)

            # Column data types
            ax.text(0.05, 0.82, "Column Data Types:", fontsize=12, fontweight="bold")
            col_dtypes = pd.DataFrame(df.dtypes.astype(str), columns=["Data Type"])
            ax.table(cellText=col_dtypes.values,
                     colLabels=col_dtypes.columns,
                     rowLabels=col_dtypes.index,
                     loc="upper left",
                     colWidths=[0.3],
                     bbox=[0.05, 0.45, 0.4, 0.35])

            # Statistical Summary
            ax.text(0.05, 0.40, "Statistical Summary:", fontsize=12, fontweight="bold")
            summary = df.describe().round(2).reset_index()
            ax.table(cellText=summary.values,
                     colLabels=summary.columns,
                     loc="upper left",
                     colWidths=[0.12]*len(summary.columns),
                     bbox=[0.05, 0.05, 0.9, 0.35])

            pdf.savefig(stats_fig, bbox_inches="tight")
            plt.close(stats_fig)

            # Page 2: Correlation Heatmap
            numeric_df = df.select_dtypes(include=["number"])
            if numeric_df.shape[1] > 1:
                corr_fig, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
                ax.set_title("Correlation Heatmap", fontsize=14, fontweight="bold")
                pdf.savefig(corr_fig, bbox_inches="tight")
                plt.close(corr_fig)

            # Page 3: Combined Dashboard
            pdf.savefig(fig, bbox_inches="tight")

        pdf_buffer.seek(0)
        st.download_button(
            label="📄 Download Final Report",
            data=pdf_buffer,
            file_name="DataVizStudio_Report.pdf",
            mime="application/pdf"
        )

    else:
        st.info("👈 Upload a CSV, JSON, or Excel file to get started.")
