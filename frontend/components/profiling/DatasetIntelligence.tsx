"use client";

import React from "react";
import { DatasetProfileResponse } from "@/types";
import { StatCard } from "@/components/ui/StatCard";
import {
  DatasetIcon,
  DataQualityIcon,
  EDAIcon,
  SQLIcon,
  StatisticsIcon,
} from "@/components/icons";

interface DatasetIntelligenceProps {
  profile: DatasetProfileResponse;
}

export function DatasetIntelligence({ profile }: DatasetIntelligenceProps) {
  return (
    <div className="grid-4" style={{ gap: "1rem" }}>
      <StatCard
        label="Dataset Dimensions"
        value={`${profile.row_count.toLocaleString()} × ${profile.column_count}`}
        subtext={`${profile.row_count.toLocaleString()} rows, ${profile.column_count} columns`}
        icon={<DatasetIcon size={16} />}
      />

      <StatCard
        label="Data Types Breakdown"
        value={`${profile.numeric_columns_count} Num / ${profile.categorical_columns_count} Cat`}
        subtext={`${profile.datetime_columns_count} temporal, ${profile.identifier_columns_count} identifier(s)`}
        icon={<StatisticsIcon size={16} />}
      />

      <StatCard
        label="ML Target Candidates"
        value={profile.target_candidates.length}
        subtext={
          profile.target_candidates.length > 0
            ? `${profile.target_candidates[0].task_type.replace("_", " ")} recommended`
            : "No obvious target variable detected"
        }
        icon={<EDAIcon size={16} />}
      />

      <StatCard
        label="Profiling Engine"
        value="DuckDB Out-Of-Core"
        subtext={`Engine: ${profile.profiling_version} (Deterministic)`}
        icon={<SQLIcon size={16} />}
      />
    </div>
  );
}
