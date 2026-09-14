"use client";

import React, { useState } from "react";
import { ForecastModelDefinition } from "@/types/forecasting";
import { Check, ChevronDown, ChevronRight, Cpu, Settings2, Sparkles } from "./icons";

interface ForecastModelSelectorProps {
  models: ForecastModelDefinition[];
  selectedModels: string[];
  setSelectedModels: (models: string[]) => void;
  modelParameters: Record<string, Record<string, any>>;
  setModelParameters: (params: Record<string, Record<string, any>>) => void;
  isAdvanced: boolean;
}

export const ForecastModelSelector: React.FC<ForecastModelSelectorProps> = ({
  models,
  selectedModels,
  setSelectedModels,
  modelParameters,
  setModelParameters,
  isAdvanced,
}) => {
  const [openDrawerModelId, setOpenDrawerModelId] = useState<string | null>(null);

  const toggleModel = (id: string) => {
    if (selectedModels.includes(id)) {
      if (selectedModels.length > 1) {
        setSelectedModels(selectedModels.filter((m) => m !== id));
      }
    } else {
      setSelectedModels([...selectedModels, id]);
    }
  };

  const handleParamChange = (modelId: string, paramKey: string, value: any) => {
    setModelParameters({
      ...modelParameters,
      [modelId]: {
        ...(modelParameters[modelId] || {}),
        [paramKey]: value,
      },
    });
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-slate-100">
            Model Selection & Parameters
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => setSelectedModels(models.map((m) => m.model_id))}
            className="text-slate-400 hover:text-indigo-300 transition-colors"
          >
            Select All
          </button>
          <span className="text-slate-700">|</span>
          <button
            type="button"
            onClick={() => setSelectedModels(["naive", "seasonal_naive", "drift"])}
            className="text-slate-400 hover:text-indigo-300 transition-colors"
          >
            Baselines Only
          </button>
        </div>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {models.map((m) => {
          const isSelected = selectedModels.includes(m.model_id);
          const hasParams = Object.keys(m.parameter_schema || {}).length > 0;

          return (
            <div
              key={m.model_id}
              className={`p-3.5 rounded-xl border transition-all text-left flex flex-col justify-between ${
                isSelected
                  ? "bg-indigo-950/20 border-indigo-500/50 shadow-sm shadow-indigo-500/10"
                  : "bg-slate-950/40 border-slate-800/80 opacity-70 hover:opacity-100"
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => toggleModel(m.model_id)}
                    className="flex items-center gap-2 font-semibold text-sm text-slate-100 text-left hover:text-indigo-300 transition-colors"
                  >
                    <div
                      className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                        isSelected
                          ? "bg-indigo-600 border-indigo-500 text-white"
                          : "border-slate-700 bg-slate-900"
                      }`}
                    >
                      {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                    </div>
                    <span>{m.display_name}</span>
                  </button>
                </div>

                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                  {m.description}
                </p>

                <div className="flex flex-wrap gap-1 pt-1">
                  {m.supports_seasonality && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">
                      Seasonal
                    </span>
                  )}
                  {m.supports_trend && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-emerald-300 font-mono">
                      Trend
                    </span>
                  )}
                  {m.supports_prediction_intervals && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-purple-300 font-mono">
                      Intervals
                    </span>
                  )}
                </div>
              </div>

              {/* Advanced Parameter Toggle */}
              {isAdvanced && hasParams && isSelected && (
                <div className="pt-3 border-t border-slate-800/60 mt-3">
                  <button
                    type="button"
                    onClick={() =>
                      setOpenDrawerModelId(
                        openDrawerModelId === m.model_id ? null : m.model_id
                      )
                    }
                    className="w-full flex items-center justify-between text-[11px] text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    <span className="flex items-center gap-1">
                      <Settings2 className="w-3 h-3" /> Parameters
                    </span>
                    {openDrawerModelId === m.model_id ? (
                      <ChevronDown className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5" />
                    )}
                  </button>

                  {/* Drawer */}
                  {openDrawerModelId === m.model_id && (
                    <div className="space-y-2 mt-2 pt-2 border-t border-slate-800/40">
                      {Object.entries(m.parameter_schema).map(([paramKey, schema]: [string, any]) => {
                        const currentVal =
                          modelParameters[m.model_id]?.[paramKey] ??
                          m.default_parameters[paramKey];

                        return (
                          <div key={paramKey} className="space-y-1">
                            <label className="text-[10px] text-slate-400 block font-mono">
                              {paramKey} ({schema.type})
                            </label>
                            {schema.type === "enum" ? (
                              <select
                                value={currentVal}
                                onChange={(e) =>
                                  handleParamChange(m.model_id, paramKey, e.target.value)
                                }
                                className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200"
                              >
                                {schema.allowed.map((opt: string) => (
                                  <option key={opt} value={opt}>
                                    {opt}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <input
                                type="number"
                                value={currentVal}
                                min={schema.min}
                                max={schema.max}
                                step={schema.type === "float" ? 0.05 : 1}
                                onChange={(e) =>
                                  handleParamChange(
                                    m.model_id,
                                    paramKey,
                                    schema.type === "float"
                                      ? parseFloat(e.target.value)
                                      : parseInt(e.target.value)
                                  )
                                }
                                className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200"
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
