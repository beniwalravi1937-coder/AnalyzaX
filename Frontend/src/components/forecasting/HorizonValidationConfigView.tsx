"use client";

import { Sliders, ShieldCheck, Target, Zap } from "./icons";

interface HorizonValidationConfigViewProps {
  horizon: number;
  setHorizon: (h: number) => void;
  windowType: string;
  setWindowType: (wt: string) => void;
  validationFolds: number;
  setValidationFolds: (vf: number) => void;
  primaryMetric: string;
  setPrimaryMetric: (m: string) => void;
  confidenceLevel: number;
  setConfidenceLevel: (cl: number) => void;
  frequencyLabel: string;
}

export const HorizonValidationConfigView: React.FC<HorizonValidationConfigViewProps> = ({
  horizon,
  setHorizon,
  windowType,
  setWindowType,
  validationFolds,
  setValidationFolds,
  primaryMetric,
  setPrimaryMetric,
  confidenceLevel,
  setConfidenceLevel,
  frequencyLabel,
}) => {
  return (
    <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-5">
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <Sliders className="w-5 h-5 text-indigo-400" />
        <h3 className="text-base font-semibold text-slate-100">
          Horizon & Validation Strategy
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Forecast Horizon */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
            <span>Forecast Horizon</span>
            <span className="text-indigo-400 font-mono font-bold">
              {horizon} {frequencyLabel.toLowerCase()} periods
            </span>
          </label>
          <input
            type="range"
            min={1}
            max={60}
            value={horizon}
            onChange={(e) => setHorizon(parseInt(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>1</span>
            <span>14</span>
            <span>30</span>
            <span>60</span>
          </div>
        </div>

        {/* Validation Folds */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
            <span>Rolling-Origin Backtest Folds</span>
            <span className="text-indigo-400 font-mono font-bold">{validationFolds} folds</span>
          </label>
          <input
            type="range"
            min={1}
            max={5}
            value={validationFolds}
            onChange={(e) => setValidationFolds(parseInt(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>1 fold</span>
            <span>3 folds</span>
            <span>5 folds</span>
          </div>
        </div>

        {/* Primary Metric */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
            <Target className="w-3.5 h-3.5 text-indigo-400" /> Primary Ranking Metric
          </label>
          <select
            value={primaryMetric}
            onChange={(e) => setPrimaryMetric(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value="rmse">RMSE (Root Mean Squared Error)</option>
            <option value="mae">MAE (Mean Absolute Error)</option>
            <option value="mase">MASE (Mean Absolute Scaled Error)</option>
            <option value="smape">sMAPE (Symmetric Percentage Error)</option>
            <option value="wape">WAPE (Weighted Absolute Percentage Error)</option>
          </select>
        </div>

        {/* Confidence Level */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" /> Prediction Interval
          </label>
          <select
            value={confidenceLevel}
            onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value={0.90}>90% Confidence Interval (±1.645σ)</option>
            <option value={0.95}>95% Confidence Interval (±1.960σ - Recommended)</option>
            <option value={0.99}>99% Confidence Interval (±2.576σ)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
