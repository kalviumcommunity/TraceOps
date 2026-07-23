# Analysis Visualizations & Business Dashboard Documentation

This directory contains five analytical visualizations designed for business stakeholders. Each chart has been crafted following business visualization principles: matching chart types to data relationships, using complete labels, applying a unified accessible color palette, and highlighting actionable insights with annotations.

---

## Chart Overview & Insight Summaries

### Chart 1: Revenue by Product Line
- **File Name:** `chart1_revenue_by_product.png`
- **Chart Type:** Horizontal Bar Chart
- **Business Question:** Which product line generates the most revenue in Q4, and how do product categories compare?
- **Key Insight:** `Cloud Solutions` is the primary revenue driver, generating **$5.2M (33.3% of total revenue)**, followed by `Analytics Platform` ($3.8M). The top two categories account for over 57% of total company revenue.
- **Annotation:** Highlights top performer `Cloud Solutions` ($5.2M) with a highlighted callout box.
- **Design Rationale:** A horizontal bar chart was chosen because category names are long, making horizontal text immediately readable without angled labels.

---

### Chart 2: Monthly Revenue Trend
- **File Name:** `chart2_revenue_trend.png`
- **Chart Type:** Multi-Series Line Chart with Reference Line
- **Business Question:** How has revenue trended over the last 12 months across key product lines?
- **Key Insight:** Steady upward trajectory across all product lines throughout 2024. `Cloud Solutions` crossed its annual target threshold ($4.5M) in September and peaked at **$5.2M** in December.
- **Annotation:**
  1. Marked **August Dip ($4.0M)** caused by seasonal summer slowdown.
  2. Highlighted **September Target Crossing ($4.6M vs $4.5M Target)**.
- **Design Rationale:** Line charts imply continuity over continuous time series. A dashed green horizontal line adds context by comparing performance against target KPIs.

---

### Chart 3: Order Value Distribution
- **File Name:** `chart3_order_value_distribution.png`
- **Chart Type:** Histogram with Mean & Median Indicators
- **Business Question:** What is the typical order value range, and are there distinct purchasing patterns?
- **Key Insight:** Order values exhibit a clear **bimodal distribution**:
  - Primary peak between **$100 - $150** (Standard Self-Serve / SMB Orders).
  - Secondary peak between **$400 - $500** (Enterprise Solution Bundles).
- **Annotation:** Annotated both bimodal peaks and included vertical reference lines for **Mean ($245.50)** and **Median ($220.00)**.
- **Design Rationale:** Histograms reveal underlying distributional shapes (bimodality and outliers) that single metric averages obscure.

---

### Chart 4: Revenue Composition by Quarter
- **File Name:** `chart4_revenue_composition.png`
- **Chart Type:** Stacked Bar Chart
- **Business Question:** How does overall quarterly revenue break down by product line composition, and where is growth coming from?
- **Key Insight:** Quarterly revenue expanded from **$10.3M in Q1** to **$14.6M in Q4 (+41.7% growth)**. Growth was disproportionately driven by `Cloud Solutions` and `AI & ML Tools`, while `Database Services` remained flat.
- **Annotation:** Marked Q4 composition surge with an arrow highlighting the expansion driven by Cloud & AI product lines.
- **Design Rationale:** Stacked bar charts communicate both total volume per quarter and internal category breakdown without cluttering the screen.

---

### Chart 5: Marketing Spend vs. Revenue Generated
- **File Name:** `chart5_marketing_vs_revenue.png`
- **Chart Type:** Scatter Plot with Linear Trendline
- **Business Question:** Does marketing spend correlate with revenue generated across campaign cohorts?
- **Key Insight:** Strong positive correlation (**r = 0.88**), indicating an average ROI multiplier of **~3.2x spend**. However, one campaign was identified as an inefficient outlier.
- **Annotation:**
  1. Marked **Outlier Campaign** (High Spend of $85K producing only $120K Revenue due to targeting misalignment).
  2. Annotated linear ROI trendline ($r = 0.88$).
- **Design Rationale:** Scatter plots visually reveal relationships between two numerical variables while making anomalies and clusters instantly recognizable.

---

## Consistent Colour Palette & Visual Language

To prevent cognitive overload, all charts use a standardized color system:

| Color Token | Hex Code | Role / Meaning |
| :--- | :--- | :--- |
| **Primary** | `#1f77b4` | Cloud Solutions / Primary Metric / Trendlines |
| **Secondary** | `#ff7f0e` | Analytics Platform / Secondary Trends |
| **Success** | `#2ca02c` | Security Suite / Target Lines / Growth Highlights |
| **Warning / Danger** | `#d62728` | Database Services / Target Threshold / Outliers |
| **Purple** | `#9467bd` | AI & ML Tools / Premium Segment / Composition Annotations |
| **Neutral / Grid** | `#7f7f7f` | Gridlines, Baselines & Secondary Labels |

### Accessibility & Color Blindness Considerations
1. **Red-Green Contrast:** High-contrast hex codes (`#1f77b4` blue vs `#d62728` red) ensure distinct visibility for red-green color blind viewers (Deuteranopia/Protanopia).
2. **Multi-Cue Encoding:** Line plots use distinct marker shapes (`o` circle, `s` square, `^` triangle) in addition to color. Scatter plots use distinct marker icons (`D` diamond for outliers).
3. **Greyscale Legibility:** All bar, line, and scatter series maintain distinct luminance values so charts remain readable when printed in greyscale.

---

## Complete Labelling Standards

Every visualization incorporates the five core labeling requirements:
1. **Title:** Descriptive title explaining what the chart shows and time period.
2. **X-Axis Label:** Clear axis name with explicit units (`Revenue ($M)`, `Spend ($K)`, `Month (2024)`).
3. **Y-Axis Label:** Explicit metric and unit specification.
4. **Legend:** Placed outside data overlap areas with high contrast background boxes.
5. **Data Labels & Formatters:** Formatted for human readability (`$5.2M`, `$250`, `%`) to eliminate cognitive load.
