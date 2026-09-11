// Pre-configured starter dashboard templates for Phase 14

export interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  iconName: string;
  badge: string;
}

export const STARTER_TEMPLATES: DashboardTemplate[] = [
  {
    id: "executive_overview",
    name: "Executive Overview",
    description: "High-level KPI metrics, operational volumes, and strategic narrative summary.",
    iconName: "dashboard",
    badge: "Recommended",
  },
  {
    id: "eda_quality",
    name: "EDA & Quality Audit",
    description: "Automated profile anomalies, nullity rates, and raw tabular observations.",
    iconName: "quality",
    badge: "Data Integrity",
  },
  {
    id: "sales_analysis",
    name: "Sales & Performance",
    description: "Multi-series trend visualization, top performers, and transaction records.",
    iconName: "chart",
    badge: "Commercial",
  },
  {
    id: "ml_forecasting",
    name: "ML & Horizon Forecasting",
    description: "Best predictive model metrics, feature importance, and temporal forecasting.",
    iconName: "ml",
    badge: "Predictive",
  },
];
