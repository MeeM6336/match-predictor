import React, { useState, useEffect, useMemo, useCallback } from 'react';
import './ModelPerformance.css';
import { fetchModelMetrics, fetchMatchPredictions } from '../assets/util/matches';
import { computeRocAuc, computeLogLoss } from '../assets/util/metrics'


const ModelPerformance = ({ model }) => {
  // State management
  const [trainingMetrics, setTrainingMetrics] = useState({});
  const [matchPredictions, setMatchPredictions] = useState([]);
  const [selectedMetricType, setSelectedMetricType] = useState("Training");

  // Event handler
  const selectMetricType = (event) => {
    setSelectedMetricType(event.target.value);
  };

  // Effect for intitial training metrics fetch
  useEffect(() => {
    const loadModelMetric = async () => {
      try {
        const metric = await fetchModelMetrics(model.model_name);
        setTrainingMetrics(metric?.[0] || null);
      } catch (err) {
        console.error(err);
        setTrainingMetrics(null);
      }
    };
    loadModelMetric();
  }, [model?.model_name]);

  // Effect to load live match predictions
  useEffect(() => {
    const loadMatchPredictions = async () => {
      try {
        const matchPredictions = await fetchMatchPredictions(model.model_id);
        setMatchPredictions(matchPredictions);
      } catch(error) {
        console.error("Error loading live metrics:", error);
        setMatchPredictions(null);
      }
    }
    loadMatchPredictions();
  }, [model?.model_id]);

  const liveMatchMetrics = useMemo(() => {
    if(!matchPredictions) return null;
    let t_neg = 0, t_pos = 0, f_neg = 0, f_pos = 0;
    const y_true = [];
    const y_prob = [];

    matchPredictions.forEach(match => {
      const { actual_outcome, prediction, confidence } = match;
      if (actual_outcome != null && prediction != null && confidence != null) {
        y_true.push(actual_outcome);
        y_prob.push(confidence);

        if (prediction === 1 && actual_outcome === 1) t_pos++;
        else if (prediction === 1 && actual_outcome === 0) f_pos++;
        else if (prediction === 0 && actual_outcome === 0) t_neg++;
        else if (prediction === 0 && actual_outcome === 1) f_neg++;
      }
    });

    return({ "f_neg": f_neg, "f_pos": f_pos, "t_neg": t_neg, "t_pos": t_pos, "y_true": y_true, "y_prob": y_prob});
  }, [matchPredictions])

  const calculateMetrics = useMemo(() => {
    if(!trainingMetrics || !liveMatchMetrics) {
      return null;
    }

    let t_neg = 0, t_pos = 0, f_neg = 0, f_pos = 0, loss = 0, roc_auc = 0;
    let y_true = [];
    let y_prob = [];

    if (selectedMetricType === "Training") {
      t_neg = trainingMetrics.t_neg;
      t_pos = trainingMetrics.t_pos;
      f_neg = trainingMetrics.f_neg;
      f_pos = trainingMetrics.f_pos;
      loss = trainingMetrics.loss
      roc_auc = trainingMetrics.roc_auc
    }

    else if (selectedMetricType === "Live") {
      const liveMetrics = liveMatchMetrics
      t_neg = liveMetrics.t_neg;
      t_pos = liveMetrics.t_pos;
      f_neg = liveMetrics.f_neg;
      f_pos = liveMetrics.f_pos;
      y_true = liveMetrics.y_true;
      y_prob = liveMetrics.y_prob;
      loss = computeLogLoss(y_true, y_prob);
      roc_auc = computeRocAuc(y_true, y_prob);
    }

    const total = t_pos + t_neg + f_pos + f_neg;

    const accuracy = total > 0 ? (t_pos + t_neg) / total : 0;
    const precision = (t_pos + f_pos) > 0 ? t_pos / (t_pos + f_pos) : 0;
    const recall = (t_pos + f_neg) > 0 ? t_pos / (t_pos + f_neg) : 0;
    const f1 = (precision + recall) > 0 ? (2 * precision * recall) / (precision + recall) : 0;

    return({ "accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1, "loss": loss, "roc_auc": roc_auc });
  }, [selectedMetricType, trainingMetrics, liveMatchMetrics]);

  // Rendering logic
  const getMatrixCellStyle = useCallback((value) => {
    const currentMetrics = selectedMetricType === 'Training' ? trainingMetrics : liveMatchMetrics;
    if (!currentMetrics || !value) return { padding: "1rem" };
    
    const maxVal = currentMetrics.t_neg + currentMetrics.t_pos + currentMetrics.f_neg + currentMetrics.f_pos;
    if (maxVal === 0) return { padding: "1rem" };

    const intensity = Math.round((value / maxVal) * 255);

    return {
      backgroundColor: `rgb(${intensity}, 0, ${255 - intensity})`,
      color: "white",
      padding: "1rem",
      paddingLeft: "3rem",
      paddingRight: "3rem",
      minWidth: "1.75rem",
      height: "2.5rem"
    };
  }, [selectedMetricType, trainingMetrics, liveMatchMetrics]);
  
  const renderMetric = (value, name) => (
    <div className='performance-metric'>
      <p className='performance-metric-number'>{typeof value === 'number' ? value.toFixed(4) : 'N/A'}</p>
      <p className='performance-metric-name'>{name}</p>
    </div>
  );

  const currentData = selectedMetricType === "Training" ? trainingMetrics : liveMatchMetrics;

  return (
    <div>
      <div className='ModelPerformance'>
        <div className='performance-header'>
          <p>Model Performance</p>
          <div>
            <select value={selectedMetricType} onChange={selectMetricType}>
              <option value="Training">Training</option>
              <option value="Live">Live</option>
            </select>
          </div>
        </div>
        {calculateMetrics ? (
          <div className='performance-metrics-container'>
            {renderMetric(calculateMetrics["accuracy"], 'Accuracy')}
            {renderMetric(calculateMetrics["precision"], 'Precision')}
            {renderMetric(calculateMetrics["recall"], 'Recall')}
            {renderMetric(calculateMetrics["f1"], 'F1-Score')}
            {renderMetric(calculateMetrics["loss"], 'Loss')}
            {renderMetric(calculateMetrics["roc_auc"], 'ROC AUC')}
          </div>
        ) : <></>}
        <div className='performance-grid-container'>
          <div className='confusion-matrix-container'>
            <p className='performance-grid-subtitle'>{selectedMetricType} Data Confusion Matrix</p>
            <div className='confusion-matrix-table-container'>
              {currentData ? (
                  <table className='confusion-matrix-table'>
                    <thead>
                      <tr>
                        <th />
                        <th>0</th>
                        <th>1</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <th style={{ paddingRight: "0.5rem" }}>0</th>
                        <td style={getMatrixCellStyle(currentData.t_neg)}>{currentData.t_neg}</td>
                        <td style={getMatrixCellStyle(currentData.f_pos)}>{currentData.f_pos}</td>
                      </tr>
                      <tr>
                        <th style={{ paddingRight: "0.5rem" }}>1</th>
                        <td style={getMatrixCellStyle(currentData.f_neg)}>{currentData.f_neg}</td>
                        <td style={getMatrixCellStyle(currentData.t_pos)}>{currentData.t_pos}</td>
                      </tr>
                    </tbody>
                  </table>
                ) : (<></>)}
            <div className='confusion-matrix-legend'></div>
          </div>
        </div>
        {model && (
          <>
            <div className='class-representation-container'>
              <p className='performance-grid-subtitle'>Class Representation Graph</p>
              <img src={`/images/${model.model_name}_${selectedMetricType}_class_representation_bar_graph.png`} />
            </div>
            <div className='class-seperation-quality-container'>
              <p className='performance-grid-subtitle'>Class Seperation Plot</p>
              <img src={`/images/${model.model_name}_${selectedMetricType}_class_seperation_quality_plot.png`} />
            </div>
            {selectedMetricType === "Training" ? (
              <div className='accuracy-graph-container'>
                <p className='performance-grid-subtitle'>Cumulative Accuracy Over Matches</p>
                <img src={`/images/${model.model_name}_Training_cumm_accuracy_graph.png`} />
              </div>
            ) : (
              <div className='accuracy-graph-container'>
                <p className='performance-grid-subtitle'>Rolling Accuracy Over Matches (Window Size: 10)</p>
                <img src={`/images/${model.model_name}_Live_rolling_accuracy_graph.png`} />
              </div>
            )}
          </>
        )}
        </div>
      </div>
    </div>
  );
};

export default ModelPerformance;