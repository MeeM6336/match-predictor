import React, { useState, useEffect, useCallback } from 'react';
import './ModelPerformance.css';
import { fetchModelMetrics, fetchMatchPredictionStats } from '../assets/util/matches';
import { computeRocAuc, computeLogLoss } from '../assets/util/metrics'


const ModelPerformance = ({ model }) => {
  // State management
  const [trainingMetrics, setTrainingMetrics] = useState(null);
  const [liveMetrics, setLiveMetrics] = useState(null);
  const [calculatedMetrics, setCalculatedMetrics] = useState(null);
  const [selectedMetricType, setSelectedMetricType] = useState("Training");
  const [loading, setLoading] = useState(false);

  // Event handler
  const selectMetricType = (event) => {
    setSelectedMetricType(event.target.value);
  };

  // Effect for intitial training metrics fetch
  useEffect(() => {
    if (!model?.model_name) return;

    const loadModelMetric = async () => {
      setLoading(true)
      try {
        const metric = await fetchModelMetrics(model.model_name);
        setTrainingMetrics(metric?.[0] || null);
      } catch (err) {
        console.error(err);
        setTrainingMetrics(null);
      } finally {
        setLoading(false)
      }
    };
    loadModelMetric();
  }, [model?.model_name]);

  // Effect to load and compute metrics
  useEffect(() => {
    if (!model?.model_id) return;

    const loadLiveMetrics = async () => {
      setLoading(true);
      try {
        const matchPredictionsStats = await fetchMatchPredictionStats(model.model_id);
        if (!matchPredictionsStats || matchPredictionsStats.length === 0) {
          setLiveMetrics(null);
          return;
        }

        let t_neg = 0, t_pos = 0, f_neg = 0, f_pos = 0;
        const y_true = [];
        const y_prob = [];

        matchPredictionsStats.forEach(match => {
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

        const loss = computeLogLoss(y_true, y_prob);
        const roc_auc = computeRocAuc(y_true, y_prob);

        setLiveMetrics({ t_neg, t_pos, f_neg, f_pos, loss, roc_auc });
      } catch (error) {
        console.error("Error loading live metrics:", error);
        setLiveMetrics(null);
      } finally {
        setLoading(false);
      }
    };

    loadLiveMetrics();
  }, [model?.model_id]);

  // Effect for calculation logic
  const calculateMetrics = useCallback((metricsData) => {
    if (!metricsData) return null;

    const { t_pos = 0, t_neg = 0, f_pos = 0, f_neg = 0, loss = 0, roc_auc = 0 } = metricsData;
    const totalPopulation = t_pos + t_neg + f_pos + f_neg;

    // FIX: Handle division by zero by defaulting to 0.
    const accuracy = totalPopulation > 0 ? (t_pos + t_neg) / totalPopulation : 0;
    const precision = (t_pos + f_pos) > 0 ? t_pos / (t_pos + f_pos) : 0;
    const recall = (t_pos + f_neg) > 0 ? t_pos / (t_pos + f_neg) : 0;
    const f1 = (precision + recall) > 0 ? (2 * precision * recall) / (precision + recall) : 0;

    return [accuracy, precision, recall, f1, loss, roc_auc];
  }, []);


  // Effect to update calculated metrics when data or selection changes
  useEffect(() => {
    const sourceMetrics = selectedMetricType === "Training" ? trainingMetrics : liveMetrics;
    const newCalculatedMetrics = calculateMetrics(sourceMetrics);
    setCalculatedMetrics(newCalculatedMetrics);
  }, [trainingMetrics, liveMetrics, selectedMetricType, calculateMetrics]);

  // Rendering logic
  const getMatrixCellStyle = useCallback((value) => {
    const currentMetrics = selectedMetricType === 'Training' ? trainingMetrics : liveMetrics;
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
  }, [selectedMetricType, trainingMetrics, liveMetrics]);
  
  const currentData = selectedMetricType === "Training" ? trainingMetrics : liveMetrics;
  
  const renderMetric = (value, name) => (
    <div className='performance-metric'>
      <p className='performance-metric-number'>{typeof value === 'number' ? value.toFixed(4) : 'N/A'}</p>
      <p className='performance-metric-name'>{name}</p>
    </div>
  );

  return (
    <div>
      {loading ? (
        <div>Loading...</div>
      ) : (
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
          {calculatedMetrics ? (
            <div className='performance-metrics-container'>
              {renderMetric(calculatedMetrics[0], 'Accuracy')}
              {renderMetric(calculatedMetrics[1], 'Precision')}
              {renderMetric(calculatedMetrics[2], 'Recall')}
              {renderMetric(calculatedMetrics[3], 'F1-Score')}
              {renderMetric(calculatedMetrics[4], 'Log Loss')}
              {renderMetric(calculatedMetrics[5], 'ROC AUC')}
            </div>
          ) : (<div></div>)}
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
      )}
    </div>
  );
};

export default ModelPerformance;