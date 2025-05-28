import React, { useState, useEffect } from 'react';
import './ModelPerformance.css';
import { fetchModelMetrics, fetchMatchPredictionStats, computeRocAuc } from '../assets/util/matches';


const ModelPerformance = ({model}) => {
  const [trainingMetrics, setTrainingMetrics] = useState();
  const [liveMetrics, setLiveMetrics] = useState();
  const [calculatedMetrics, setCalculatedMetrics] = useState();
  const [selectedMetricType, setSelectedMetricType] = useState("Training")

  const selectMetricType = (event) => {
    setSelectedMetricType(event.target.value);
  };

  useEffect(() => {
    const loadModelMetric = async () => {
      const metric = await fetchModelMetrics(model);
      setTrainingMetrics(metric[0]);
    };

    loadModelMetric();
  }, []);

  useEffect (() => {
    const loadLiveMetrics = async () => {
      const matchPredictionsStats = await fetchMatchPredictionStats();
      let t_neg = 0, t_pos = 0, f_neg = 0, f_pos = 0;
      const y_true = [];
      const y_prob = [];

      if(!matchPredictionsStats)
        return;

      matchPredictionsStats.forEach(match => {
        const actual = match.actual_outcome;
        const predicted = match.outcome;
        const confidence = match.confidence;

        if (actual != null && predicted != null && confidence != null) {
          y_true.push(actual);
          y_prob.push(confidence);

          if (predicted == 1 && actual == 1) t_pos++;
          else if (predicted == 1 && actual == 0) f_pos++;
          else if (predicted == 0 && actual == 0) t_neg++;
          else if (predicted == 0 && actual == 1) f_neg++;
        }
      });

      const computeLogLoss = (y_true, y_prob) => {
        const eps = 1e-15;
        let loss = 0;
        for (let i = 0; i < y_true.length; i++) {
          const y = y_true[i];
          const p = Math.min(Math.max(y_prob[i], eps), 1 - eps);
          loss += y * Math.log(p) + (1 - y) * Math.log(1 - p);
        }
        return -loss / y_true.length;
      };
      const log_loss = computeLogLoss(y_true, y_prob)
      const roc_auc = computeRocAuc(y_true, y_prob);

      setLiveMetrics({t_neg, t_pos, f_neg, f_pos, log_loss, roc_auc});
    }

    loadLiveMetrics();
  }, []);

  useEffect(() => {
    if(!trainingMetrics && !liveMetrics)
      return;

    let accuracy, precision, recall, f1, log_loss, roc_auc;

    if (selectedMetricType == "Training") {
      accuracy = (trainingMetrics.t_pos + trainingMetrics.t_neg)/(trainingMetrics.t_pos + trainingMetrics.t_neg + trainingMetrics.f_neg + trainingMetrics.f_pos);
      precision = (trainingMetrics.t_pos)/(trainingMetrics.t_pos + trainingMetrics.f_pos);
      recall = (trainingMetrics.t_pos)/(trainingMetrics.t_pos + trainingMetrics.f_neg);
      f1 = (2 * precision * recall)/(precision + recall);
      log_loss = trainingMetrics.log_loss;
      roc_auc = trainingMetrics.roc_auc;
    }

    else if (selectedMetricType == "Live") {
      accuracy = (liveMetrics.t_pos + liveMetrics.t_neg)/(liveMetrics.t_pos + liveMetrics.t_neg + liveMetrics.f_neg + liveMetrics.f_pos);
      precision = (liveMetrics.t_pos)/(liveMetrics.t_pos + liveMetrics.f_pos);
      recall = (liveMetrics.t_pos)/(liveMetrics.t_pos + liveMetrics.f_neg);
      f1 = (2 * precision * recall)/(precision + recall);
      log_loss = liveMetrics.log_loss;
      roc_auc = liveMetrics.roc_auc;
    }

    setCalculatedMetrics([accuracy, precision, recall, f1, log_loss, roc_auc]);

  }, [trainingMetrics, liveMetrics, selectedMetricType])

  const getMatrixCellStyle = (value) => {
    const maxVal = trainingMetrics['t_neg'] + trainingMetrics['t_pos'] + trainingMetrics['f_neg'] + trainingMetrics['f_pos'];
    
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
  };

  return (
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
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[0]).toFixed(4)}</p>
            <p className='performance-metric-name'>Accuracy</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[1]).toFixed(4)}</p>
            <p className='performance-metric-name'>Precision</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[2]).toFixed(4)}</p>
            <p className='performance-metric-name'>Recall</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[3]).toFixed(4)}</p>
            <p className='performance-metric-name'>F1-Score</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[4]).toFixed(4)}</p>
            <p className='performance-metric-name'>Log Loss</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[5]).toFixed(4)}</p>
            <p className='performance-metric-name'>ROC AUC</p>
          </div>
        </div>
      ) : (<div></div>)}
        <div className='performance-grid-container'>
          <div className='confusion-matrix-container'>
            <p className='performance-grid-subtitle'>{selectedMetricType} Data Confusion Matrix</p>
            <div className='confusion-matrix-table-container'>
              <table className='confusion-matrix-table'>
                <thead>
                  <tr>
                    <th></th>
                    <th>0</th>
                    <th>1</th>
                  </tr>
                </thead>
                {liveMetrics ? (
                  selectedMetricType == "Training" ? (
                    <tbody>
                      <tr>
                        <th style={{paddingRight: "0.5rem"}}>0</th>
                        <td style={getMatrixCellStyle(trainingMetrics.t_neg)}>{trainingMetrics.t_neg}</td>
                        <td style={getMatrixCellStyle(trainingMetrics.f_pos)}>{trainingMetrics.f_pos}</td>
                      </tr>
                      <tr>
                        <th style={{paddingRight: "0.5rem"}}>1</th>
                        <td style={getMatrixCellStyle(trainingMetrics.f_neg)}>{trainingMetrics.f_neg}</td>
                        <td style={getMatrixCellStyle(trainingMetrics.t_pos)}>{trainingMetrics.t_pos}</td>
                      </tr>
                    </tbody>
                  ) : (
                    <tbody>
                      <tr>
                        <th>0</th>
                        <td style={getMatrixCellStyle(liveMetrics.t_neg)}>{liveMetrics.t_neg}</td>
                        <td style={getMatrixCellStyle(liveMetrics.f_pos)}>{liveMetrics.f_pos}</td>
                      </tr>
                      <tr>
                        <th>1</th>
                        <td style={getMatrixCellStyle(liveMetrics.f_neg)}>{liveMetrics.f_neg}</td>
                        <td style={getMatrixCellStyle(liveMetrics.t_pos)}>{liveMetrics.t_pos}</td>
                      </tr>
                    </tbody>
                  )
                  ) : (<tbody></tbody>)}
              </table>
            <div className='confusion-matrix-legend'></div>
          </div>
        </div>
        <div className='class-representation-container'>
          <p className='performance-grid-subtitle'>Class Representation Graph</p>
          <img src={`/images/${model}_${selectedMetricType}_class_representation_bar_graph.png`}/>
        </div>
        <div className='class-seperation-quality-container'>
          <p className='performance-grid-subtitle'>Class Seperation Plot</p>
          <img src={`/images/${model}_${selectedMetricType}_class_seperation_quality_plot.png`}/>
        </div>
        {selectedMetricType == "Training" ? (
          <div className='accuracy-graph-container'>
            <p className='performance-grid-subtitle'>Cumulative Accuracy Over Matches</p>
            <img src={`/images/${model}_Training_cumm_accuracy_graph.png`}/>
          </div>
        ) : (
          <div className='accuracy-graph-container'>
            <p className='performance-grid-subtitle'>Rolling Accuracy Over Matches (Window Size: 10)</p>
            <img src={`/images/${model}_Live_rolling_accuracy_graph.png`}/>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelPerformance